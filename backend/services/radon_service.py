"""
Radon service — complexity & maintainability metrics.

Unlike pylint/bandit, radon has a clean Python API, so no subprocess.

Two things we measure:
1. Cyclomatic complexity per function (how many paths through the code).
   1-5 simple / 6-10 ok / 11-20 getting hairy / 21+ refactor now.
2. Maintainability Index for the whole file (0-100).
   100-85 very maintainable / 84-65 ok / below 65 hard to maintain.
"""

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze as raw_analyze

COMPLEXITY_WARN = 10   # flag functions above this
COMPLEXITY_CRITICAL = 20


def run_radon(file_path: str) -> tuple[list[dict], dict]:
    """
    Returns (findings, metrics).
    findings -> issues for overly complex functions / low maintainability
    metrics  -> numbers for the dashboard (LOC, avg complexity, MI score)
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
        code = fh.read()

    findings: list[dict] = []
    metrics: dict = {}

    try:
        # --- Raw metrics: lines of code, comments, blanks ---
        raw = raw_analyze(code)
        metrics["loc"] = raw.loc
        metrics["source_lines"] = raw.sloc
        metrics["comment_lines"] = raw.comments

        # --- Cyclomatic complexity per function/method ---
        blocks = cc_visit(code)
        complexities = [b.complexity for b in blocks]
        metrics["avg_complexity"] = (
            round(sum(complexities) / len(complexities), 2) if complexities else 0
        )
        metrics["max_complexity"] = max(complexities) if complexities else 0

        for b in blocks:
            if b.complexity > COMPLEXITY_CRITICAL:
                sev = "high"
            elif b.complexity > COMPLEXITY_WARN:
                sev = "medium"
            else:
                continue
            findings.append({
                "source": "radon",
                "severity": sev,
                "issue": f"High complexity: {b.name}() has cyclomatic complexity {b.complexity}",
                "explanation": (
                    f"'{b.name}' has {b.complexity} independent paths through it. "
                    "Complex functions are harder to test and hide bugs."
                ),
                "suggestion": "Break this function into smaller, single-purpose functions.",
                "line_number": b.lineno,
            })

        # --- Maintainability index (whole file) ---
        mi = mi_visit(code, multi=True)
        metrics["maintainability_index"] = round(mi, 1)
        if mi < 65:
            findings.append({
                "source": "radon",
                "severity": "medium",
                "issue": f"Low maintainability index ({round(mi, 1)}/100)",
                "explanation": "Score below 65 suggests this file is hard to maintain "
                               "(long, complex, or under-commented).",
                "suggestion": "Split large blocks into functions and add docstrings.",
                "line_number": None,
            })

    except (SyntaxError, Exception) as exc:  # noqa: BLE001 - analysis must never crash the app
        findings.append({
            "source": "radon",
            "severity": "info",
            "issue": "Radon could not fully analyze this file",
            "explanation": str(exc)[:300],
            "suggestion": None,
            "line_number": None,
        })

    return findings, metrics
