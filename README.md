# ai-starter

Runnable starter for a simple AI customer project.

One page collects a short message. FastAPI validates it, `ai-core` runs a structured OpenAI call, PostgreSQL stores metadata (never the raw text), and the UI shows the result.

## 1. Clone

```bash
git clone https://github.com/siinanXD/ai-starter.git
cd ai-starter
```

## 2. Env setup

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` for a live analyze call. Leave Langfuse unset unless you want traces.

## 3. Start PostgreSQL

```bash
docker compose up -d
```

## 4. Migrations

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
alembic upgrade head
```

## 5. Start FastAPI

From `apps/api`:

```bash
uvicorn app.main:app --reload --port 8000
```

`GET /health` is liveness. `GET /ready` checks the database.

## 6. Start Next.js

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000. The page posts to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## 7. Tests

From `apps/api`. OpenAI is mocked.

```bash
ruff check .
ruff format --check .
pytest
```

## 8. Evals

Default CI evals are deterministic and do not call OpenAI.

From the repo root, with `apps/api` installed and `PYTHONPATH=apps/api`:

```bash
pip install "agent-eval-harness @ git+https://github.com/siinanXD/agent-eval-harness.git@4b2cb9b7839da8970bdbf271769cde41d7258b60"
agent-eval-harness evals/suites/analyze.json \
  --target evals.target:build_target \
  --baseline analyze-baseline \
  --root .evals
```

Live OpenAI evals are opt-in only:

```bash
RUN_OPENAI_EVAL=1 OPENAI_API_KEY=... agent-eval-harness evals/suites/analyze.json \
  --target evals.live_target:build_target \
  --providers openai \
  --no-gate
```

## 9. Architecture

See `docs/ARCHITECTURE.md`.

- `ai-core` is imported for OpenAI, structured output, retry, wrapping, redaction, cost, and optional Langfuse.
- `agent-eval-harness` is the only eval runner.
- Compose runs PostgreSQL only.

## 10. Railway

See `docs/RAILWAY.md`. Dockerfiles exist for `web` and `api`. This repository does not deploy.

Pinned runtime libraries:

- `ai-core` @ `9fb7f568640346d7ba31eeb6e4d366f6a0e022f1`
- `agent-eval-harness` @ `4b2cb9b7839da8970bdbf271769cde41d7258b60`
