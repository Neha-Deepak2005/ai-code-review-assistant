# Wiring in the AI review — 4 steps

## 1. File placement
Put `ai_service.py` into `backend/services/` (next to `pylint_service.py` etc).

## 2. Add one dependency
Add this line to `backend/requirements.txt`, then run `pip install -r requirements.txt`
(with your venv activated):

```
requests==2.32.3
```

## 3. Hook it into the review run
In `routes/review.py`, inside the endpoint that runs a review — right after the
static analysis produces its findings and BEFORE the score is computed — add:

```python
from services.ai_service import run_ai_review, AIReviewError

# ... after static analysis, for each analyzed file:
try:
    ai_findings = run_ai_review(code_text, filename, static_findings=findings)
    findings.extend(ai_findings)
except AIReviewError as exc:
    # AI failure should not kill the review — keep the static results
    print(f"AI review skipped: {exc}")
```

Notes:
- `code_text` = the file's source as a string, `filename` = its name.
- The returned dicts have keys: source, severity, file_name, line_number,
  issue, suggestion. If your ReviewFinding rows use slightly different key
  names, rename them where you save findings to the DB.
- Because the AI findings carry `source="ai"`, your existing findings table
  and UI display them with zero changes — that was the whole point of the
  `source` column.

## 4. Quick test without Flask
From the `backend` folder (venv active):

```
python -m services.ai_service ..\bad_code.py
```

(point it at your deliberately-bad demo file — expect findings like the
hardcoded password and eval() usage, with fix suggestions.)

## Talking points for your review/demo
- "AI findings share one table with static findings via a `source` column."
- "The static tool output is included in the AI prompt so the model adds
  insight instead of repeating pylint."
- "The service is provider-agnostic: model, URL, and key come from env vars,
  and Groq's endpoint is OpenAI-compatible."
- "LLM output is parsed defensively — fences stripped, JSON validated,
  severities normalized — and an AI outage degrades gracefully to
  static-only results."
