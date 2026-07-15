"""
Analyzer — the orchestrator.

Given a project folder, runs every .py file through:
    pylint  (bugs & code quality)
    bandit  (security)
    radon   (complexity & maintainability)
    AI      (Groq / Llama 3.3 — logic, design, and fix suggestions)

then merges everything and computes an overall 0-100 quality score.

Scoring: start at 100 and subtract per finding, weighted by severity.
Simple, explainable, good enough — and 'explainable' is a feature when
your mentor asks "how is the score calculated?"

The AI step is fail-soft: if the provider is down, the key is missing, or
the rate limit is hit, the review completes with static findings only.
"""

import os

from services.pylint_service import run_pylint
from services.bandit_service import run_bandit
from services.radon_service import run_radon
from services.ai_service import run_ai_review, AIReviewError

SEVERITY_PENALTY = {
    "critical": 15,
    "high": 8,
    "medium": 3,
    "low": 1,
    "info": 0,
}


def analyze_project(folder: str) -> dict:
    """
    Analyze every .py file in `folder`.
    Returns {"findings": [...], "metrics": {...}, "score": int, "summary": str}
    """
    all_findings: list[dict] = []
    combined_metrics = {
        "loc": 0, "source_lines": 0, "comment_lines": 0,
        "avg_complexity": 0, "max_complexity": 0,
        "maintainability_index": None, "files_analyzed": 0,
    }
    mi_scores = []
    ai_skipped_reason = None

    py_files = sorted(
        f for f in os.listdir(folder)
        if f.endswith(".py") and os.path.isfile(os.path.join(folder, f))
    )

    for name in py_files:
        path = os.path.join(folder, name)

        # --- Static tools ---
        file_findings: list[dict] = []

        for finding in run_pylint(path) + run_bandit(path):
            finding["file_name"] = name
            file_findings.append(finding)

        radon_findings, metrics = run_radon(path)
        for finding in radon_findings:
            finding["file_name"] = name
            file_findings.append(finding)

        # --- AI review (sees the code AND what the static tools found) ---
        try:
            with open(path, encoding="utf-8") as fh:
                code_text = fh.read()
            ai_findings = run_ai_review(
                code_text, name, static_findings=file_findings
            )
            file_findings.extend(ai_findings)
        except AIReviewError as exc:
            # Fail-soft: log it, keep the static results, note it in the summary
            ai_skipped_reason = str(exc)
            print(f"[analyzer] AI review skipped for {name}: {exc}")

        all_findings.extend(file_findings)

        # --- Metrics ---
        combined_metrics["loc"] += metrics.get("loc", 0)
        combined_metrics["source_lines"] += metrics.get("source_lines", 0)
        combined_metrics["comment_lines"] += metrics.get("comment_lines", 0)
        combined_metrics["max_complexity"] = max(
            combined_metrics["max_complexity"], metrics.get("max_complexity", 0)
        )
        if metrics.get("maintainability_index") is not None:
            mi_scores.append(metrics["maintainability_index"])
        combined_metrics["files_analyzed"] += 1

    if mi_scores:
        combined_metrics["maintainability_index"] = round(
            sum(mi_scores) / len(mi_scores), 1
        )

    # ---- Score ----
    score = 100
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in all_findings:
        sev = f.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
        score -= SEVERITY_PENALTY.get(sev, 0)
    score = max(0, score)

    summary = (
        f"Analyzed {combined_metrics['files_analyzed']} file(s), "
        f"{combined_metrics['loc']} lines. Found {len(all_findings)} issue(s): "
        f"{counts['critical']} critical, {counts['high']} high, "
        f"{counts['medium']} medium, {counts['low']} low. "
        f"Quality score: {score}/100."
    )
    if ai_skipped_reason:
        summary += f" (AI review unavailable: {ai_skipped_reason[:120]})"

    return {
        "findings": all_findings,
        "metrics": combined_metrics,
        "score": score,
        "summary": summary,
    }