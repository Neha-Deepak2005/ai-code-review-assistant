"""
Pylint service — code quality & bug detection.

We run pylint as a subprocess with --output-format=json, which gives us
structured data instead of terminal text we'd have to parse by hand.

Pylint message types -> our severity scale:
    error       -> high     (probably a real bug)
    warning     -> medium   (suspicious code)
    convention  -> low      (style: naming, docstrings...)
    refactor    -> low      (could be written better)
    fatal       -> critical (pylint couldn't even parse the file)
"""

import json
import subprocess
import sys

SEVERITY_MAP = {
    "fatal": "critical",
    "error": "high",
    "warning": "medium",
    "convention": "low",
    "refactor": "low",
    "info": "info",
}


def run_pylint(file_path: str) -> list[dict]:
    """Run pylint on one file, return a list of finding dicts."""
    result = subprocess.run(
        [sys.executable, "-m", "pylint", file_path, "--output-format=json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Note: pylint exits non-zero whenever it finds ANY issue, so we
    # can't treat a non-zero exit code as a crash. Just parse stdout.
    try:
        messages = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return [{
            "source": "pylint",
            "severity": "info",
            "issue": "Pylint could not analyze this file",
            "explanation": (result.stderr or "")[:500],
            "suggestion": None,
            "line_number": None,
        }]

    findings = []
    for m in messages:
        findings.append({
            "source": "pylint",
            "severity": SEVERITY_MAP.get(m.get("type"), "info"),
            "issue": f"{m.get('symbol', 'issue')}: {m.get('message', '')}"[:300],
            "explanation": f"Pylint rule {m.get('message-id', '')} ({m.get('symbol', '')})",
            "suggestion": None,  # the AI review (Day 8) will fill suggestions in
            "line_number": m.get("line"),
        })
    return findings
