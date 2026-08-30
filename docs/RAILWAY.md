# Railway preparation

Do not deploy from this repository automatically.

`POST /api/v1/analyze` is unauthenticated and spends the OpenAI key. Do not expose the API on a public URL without a gateway or other access control.

Create three Railway services from the same GitHub repo:

| Service | Source | Root Directory | Notes |
| --- | --- | --- | --- |
| postgres | Railway PostgreSQL plugin | — | Railway's `DATABASE_URL` (`postgresql://…`) is rewritten to `postgresql+psycopg://` at startup |
| api | `Dockerfile` | `apps/api` | Installs `git` so `ai-core` can be fetched. Runs Alembic then uvicorn. Two replicas can race on the Alembic lock. |
| web | `Dockerfile` | `apps/web` | Set `NEXT_PUBLIC_API_URL` to the public API URL **at build time** |

API environment:

- `DATABASE_URL` (Railway Postgres plugin value is fine)
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional, default `gpt-4o-mini`)
- `CORS_ORIGINS` (the web origin)
- optional Langfuse keys
- optional `OPENAI_INPUT_USD_PER_MTOK` / `OPENAI_OUTPUT_USD_PER_MTOK`

Web environment:

- `NEXT_PUBLIC_API_URL`

No Redis, workers, or extra datastores. `ai-core` is public.
