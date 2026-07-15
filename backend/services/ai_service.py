"""AI code review service (Groq / Llama 3.3 70B).
 
Sends source code + the static-analysis findings to the LLM and gets back
structured findings in the same shape as the pylint/bandit/radon services,
tagged with source="ai" so they slot straight into the review_findings table.
 
Uses Groq's OpenAI-compatible chat completions endpoint via plain `requests`,
so switching provider later (company OpenAI key, etc.) only means changing
GROQ_API_URL / AI_MODEL / the key — no code changes.
"""
 
import json
import os
import re
 
import requests
 
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
 
VALID_SEVERITIES = {"critical", "high", "medium", "low"}
 
SYSTEM_PROMPT = """You are a senior Python code reviewer. You will receive a Python file
and (optionally) findings from static analysis tools (pylint, bandit, radon).
 
Review the code for: bugs, security vulnerabilities, performance problems,
bad practices, and readability issues. Do NOT repeat issues the static tools
already found — add insight they can't: logic errors, design problems,
misuse of APIs, missing error handling, and concrete fix suggestions.
 
Respond with ONLY a JSON array (no markdown fences, no commentary).
Each element must have exactly these keys:
  "severity":    one of "critical", "high", "medium", "low"
  "line_number": integer line number the issue starts at (or null if file-wide)
  "issue":       one-sentence description of the problem
  "suggestion":  one- or two-sentence concrete fix
 
Return at most 10 findings, most important first.
If the code is genuinely fine, return [].
"""
 
 
class AIReviewError(Exception):
    """Raised when the AI review cannot be completed."""
 
 
def _build_user_prompt(code: str, filename: str, static_findings: list | None) -> str:
    parts = [f"File: {filename}\n\n```python\n{code}\n```"]
    if static_findings:
        lines = [
            f"- [{f.get('source', '?')}/{f.get('severity', '?')}] "
            f"line {f.get('line_number', '?')}: {f.get('issue', '')}"
            for f in static_findings[:30]  # cap so huge reports don't blow up the prompt
        ]
        parts.append("Static analysis already found:\n" + "\n".join(lines))
    return "\n\n".join(parts)
 
 
def _extract_json_array(text: str) -> list:
    """Parse the model output defensively: strip markdown fences,
    and if extra prose sneaks in, pull out the first [...] block."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise AIReviewError(f"Model did not return valid JSON: {text[:200]}")
 
 
def _normalize(raw_findings: list, filename: str) -> list[dict]:
    """Validate/clean model output into review_findings-shaped dicts."""
    findings = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity", "low")).lower()
        if severity not in VALID_SEVERITIES:
            severity = "low"
        line = item.get("line_number")
        line = int(line) if isinstance(line, (int, float)) and line and line > 0 else None
        issue = str(item.get("issue", "")).strip()
        if not issue:
            continue
        findings.append({
            "source": "ai",
            "severity": severity,
            "file_name": filename,
            "line_number": line,
            "issue": issue[:500],
            "suggestion": str(item.get("suggestion", "")).strip()[:1000],
        })
    return findings
 
 
def run_ai_review(code: str, filename: str, static_findings: list | None = None) -> list[dict]:
    """Review one Python file. Returns a list of finding dicts (source="ai").
 
    Raises AIReviewError on configuration/network/parsing problems so the
    caller can decide whether to fail the review or continue with
    static-only results.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AIReviewError("GROQ_API_KEY is not set (check backend/.env)")
 
    payload = {
        "model": AI_MODEL,
        "temperature": 0.2,  # reviews should be consistent, not creative
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(code, filename, static_findings)},
        ],
    }
 
    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise AIReviewError(f"Could not reach the AI provider: {exc}") from exc
 
    if resp.status_code == 429:
        raise AIReviewError("AI provider rate limit hit — wait a minute and retry")
    if resp.status_code == 401:
        raise AIReviewError("AI provider rejected the API key — check GROQ_API_KEY")
    if resp.status_code != 200:
        raise AIReviewError(f"AI provider error {resp.status_code}: {resp.text[:200]}")
 
    try:
        content = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise AIReviewError("Unexpected response shape from AI provider") from exc
 
    return _normalize(_extract_json_array(content), filename)
 
 
if __name__ == "__main__":
    # Standalone smoke test:  python -m services.ai_service path/to/some_file.py
    import sys
    from dotenv import load_dotenv
 
    load_dotenv()
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not target:
        print("Usage: python -m services.ai_service <file.py>")
        sys.exit(1)
    with open(target, encoding="utf-8") as fh:
        source = fh.read()
    results = run_ai_review(source, os.path.basename(target))
    print(f"{len(results)} AI findings:")
    for f in results:
        print(f"  [{f['severity']}] line {f['line_number']}: {f['issue']}")
        print(f"      fix: {f['suggestion']}")