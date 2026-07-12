"""
Bandit service — security vulnerability scanning.

Bandit looks for things like hardcoded passwords, use of eval(),
SQL injection patterns, weak cryptography, etc.

Bandit severity -> our scale (security issues are weighted up,
because a security hole matters more than a style nit):
    HIGH   -> critical
    MEDIUM -> high
    LOW    -> medium
"""

import json
import subprocess
import sys

SEVERITY_MAP = {
    "HIGH": "critical",
    "MEDIUM": "high",
    "LOW": "medium",
}


def run_bandit(file_path: str) -> list[dict]:
    """Run bandit on one file, return a list of finding dicts."""
    result = subprocess.run(
        [sys.executable, "-m", "bandit", "-f", "json", file_path],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        report = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []

    findings = []
    for r in report.get("results", []):
        findings.append({
            "source": "bandit",
            "severity": SEVERITY_MAP.get(r.get("issue_severity"), "medium"),
            "issue": f"Security: {r.get('issue_text', '')}"[:300],
            "explanation": (
                f"Bandit check {r.get('test_id', '')} ({r.get('test_name', '')}). "
                f"Confidence: {r.get('issue_confidence', 'UNKNOWN')}. "
                f"More info: {r.get('more_info', '')}"
            ),
            "suggestion": None,
            "line_number": r.get("line_number"),
        })
    return findings
