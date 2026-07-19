# AI Code Review Assistant

A full-stack web application that reviews Python code the way a senior
developer would: it combines classic static analysis (pylint, bandit, radon)
with an LLM-powered review (Llama 3.3 70B via Groq) to find bugs, security
vulnerabilities, and design problems — then explains each issue and suggests
a concrete fix. It can also generate Markdown documentation for undocumented
code.

Built as my internship project (2026).

## Features

- **User accounts** — register/login with JWT authentication (Flask-JWT-Extended, bcrypt password hashing)
- **Project uploads** — upload one or more `.py` files, or paste code directly
- **Static analysis** — pylint (code quality), bandit (security), radon (complexity & maintainability)
- **AI code review** — the code *and* the static findings are sent to Llama 3.3 70B, which adds issues the pattern-based tools can't see (logic errors, design problems, severity judgment) with concrete fix suggestions
- **Unified findings** — static and AI findings share one schema and table, distinguished by a `source` column, so the UI needs no special cases
- **Quality score** — 0–100, computed transparently: start at 100, subtract a penalty per finding weighted by severity
- **AI documentation generator** — one click produces Markdown docs (overview, per-function parameters/returns, usage example) for any project, even fully uncommented code
- **Interactive report** — score ring, severity distribution with click-to-filter, findings table with line numbers and suggestions

## Architecture

```
frontend (React + Vite + Tailwind)
   │  axios, JWT in Authorization header
   ▼
backend (Flask REST API)
   ├── routes/      auth, upload, review, docs (blueprints)
   ├── services/    pylint_service, bandit_service, radon_service,
   │                ai_service (review), docs_service, analyzer (orchestrator)
   └── models/      User, Project, Review, ReviewFinding (SQLAlchemy)
   │
   ├── SQLite (dev) / PostgreSQL-ready via DATABASE_URL
   └── Groq API (OpenAI-compatible) — Llama 3.3 70B
```

Design decisions worth noting:

- **Provider-agnostic AI layer.** The AI services read the model name, endpoint
  URL, and key from environment variables and speak the OpenAI-compatible
  chat format — switching from Groq to OpenAI or any compatible provider is a
  config change, not a code change.
- **Fail-soft AI.** If the AI provider is unreachable or rate-limited, reviews
  still complete with static-only results and the summary notes why.
- **Defensive LLM parsing.** Model output is validated: markdown fences
  stripped, JSON extracted and schema-checked, severities normalized. The app
  never trusts the model blindly.

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free Groq API key (https://console.groq.com → API Keys)

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash; on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # then edit .env — see below
python app.py                     # http://localhost:5000
```

Edit `backend/.env`:

```
SECRET_KEY=<long random string>
JWT_SECRET_KEY=<different long random string>
GROQ_API_KEY=<your Groq key>
```

The real `.env` is git-ignored and must never be committed.

### Frontend

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

The Vite dev server proxies `/api/*` to the Flask backend.

## Usage

1. Register an account and log in
2. Create a project by uploading `.py` files (or pasting code)
3. **Run analysis** — get the score, severity distribution, and findings from
   all four sources; findings tagged `ai` include the LLM's fix suggestions
4. **Generate docs** — get Markdown documentation for the project's code,
   with a copy button

## Scoring

`score = max(0, 100 − Σ penalty(severity))` with penalties:
critical 15 · high 8 · medium 3 · low 1 · info 0.

Simple and explainable by design: every point lost traces to a specific
finding in the table.

## Security notes

- Passwords hashed with bcrypt; sessions via short-lived JWTs
- Secrets live in `.env` (git-ignored); an `.env.example` documents the
  required variables with placeholders
- Uploaded files are stored per-user and analyzed in-place; only `.py` files
  are accepted

## Tech stack

Flask · SQLAlchemy · Flask-JWT-Extended · pylint · bandit · radon ·
Groq (Llama 3.3 70B) · React · Vite · Tailwind CSS · axios
**Live demo:** https://ai-code-review-assistant-pjkc.onrender.com
