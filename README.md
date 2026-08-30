# ai-starter

Runnable starter for a simple AI customer project.

One page collects a short message. FastAPI validates it, `ai-core` runs a structured OpenAI call, PostgreSQL stores metadata only (hash, category, confidence, model, tokens — never raw input or model free-text), and the UI shows the result.

## 1. Clone

```bash
git clone https://github.com/siinanXD/ai-starter.git
cd ai-starter
```

## 2. Secrets and local environment

Preferred setup: keep user-managed application secrets in **Infisical** and inject them at runtime. See `docs/SECRETS.md`.

For a project created from this starter:

```bash
infisical login
infisical init
```

Then run the API with the `dev` secrets instead of copying `.env` files between devices. The generic starter intentionally does not commit a fixed `.infisical.json`, because each downstream project should connect to its own Infisical project.

`.env.example` remains the safe variable reference and fallback for temporary local demos:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` for a live analyze call. Leave Langfuse unset unless you want traces. Never commit or synchronize the resulting `.env` file.

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

From `apps/api`, either use variables already present in your shell or inject Infisical secrets:

```powershell
infisical run --env=dev --path=/common --path=/api --project-config-dir=../.. -- uvicorn app.main:app --reload --port 8000
```

Without Infisical, the existing command still works when the environment is configured locally:

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

Open http://localhost:3000. The page posts to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). This value is public configuration, not a secret.

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

## 10. Deployment

Default deployment split for projects created from this starter:

- **Vercel** for `apps/web` (Next.js), including pull-request Preview Deployments.
- **Railway** for `apps/api` and PostgreSQL.
- `main` is the production branch; production deployment follows a human-reviewed merge.
- User-managed runtime secrets should be synced from Infisical where practical; platform-generated values remain owned by the platform.

See `docs/DEPLOYMENT.md`, `docs/SECRETS.md`, and `docs/RAILWAY.md`.

The analyze endpoint is unauthenticated and spends the OpenAI key. Do not expose it publicly without a gateway; details are in `docs/RAILWAY.md`.

Pinned runtime libraries (both public):

- `ai-core` @ `9fb7f568640346d7ba31eeb6e4d366f6a0e022f1`
- `agent-eval-harness` @ `4b2cb9b7839da8970bdbf271769cde41d7258b60`

`pip install -e ".[dev]"` from `apps/api` is enough. The API image installs `git` so the same pin works in Docker/Railway.
