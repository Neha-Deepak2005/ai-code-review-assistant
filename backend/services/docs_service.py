"""Documentation generator service (Groq / Llama 3.3).
 
Day 10 feature: given a Python file, ask the LLM to write Markdown
documentation — overview, per-function/class docs, usage example.
 
Same provider pattern as ai_service.py: OpenAI-compatible endpoint,
config from env vars, defensive error handling.
"""
 
import os
 
import requests
 
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
 
SYSTEM_PROMPT = """You are a senior Python developer writing documentation for a codebase.
 
Given a Python file, produce clear Markdown documentation containing:
1. **Overview** — 2-3 sentences on what the file does as a whole
2. **Functions & classes** — for each one: purpose, parameters (name, type,
   meaning), return value, and any exceptions raised
3. **Usage example** — a short, realistic code snippet showing how the main
   function(s) would be called
 
Write for a developer who has never seen this code. Be accurate — document
what the code actually does, not what it should do. If the code has bugs or
odd behavior, document the actual behavior.
 
Respond with ONLY the Markdown documentation. No preamble, no code fences
around the whole response.
"""
 
 
class DocsError(Exception):
    """Raised when documentation generation cannot be completed."""
 
 
def generate_docs(code: str, filename: str) -> str:
    """Generate Markdown documentation for one Python file.
 
    Returns the documentation as a Markdown string.
    Raises DocsError on configuration/network/provider problems.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise DocsError("GROQ_API_KEY is not set (check backend/.env)")
 
    payload = {
        "model": AI_MODEL,
        "temperature": 0.3,
        "max_tokens": 2500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"File: {filename}\n\n```python\n{code}\n```"},
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
        raise DocsError(f"Could not reach the AI provider: {exc}") from exc
 
    if resp.status_code == 429:
        raise DocsError("AI provider rate limit hit — wait a minute and retry")
    if resp.status_code == 401:
        raise DocsError("AI provider rejected the API key — check GROQ_API_KEY")
    if resp.status_code != 200:
        raise DocsError(f"AI provider error {resp.status_code}: {resp.text[:200]}")
 
    try:
        content = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise DocsError("Unexpected response shape from AI provider") from exc
 
    return content.strip()
 
 
if __name__ == "__main__":
    # Standalone smoke test:  python -m services.docs_service path/to/file.py
    import sys
    from dotenv import load_dotenv
 
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: python -m services.docs_service <file.py>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as fh:
        source = fh.read()
    print(generate_docs(source, os.path.basename(sys.argv[1])))
 






