# Railway preparation

Do not deploy from this repository automatically.

Create three Railway services from the same GitHub repo:

| Service | Source | Notes |
| --- | --- | --- |
| postgres | Railway PostgreSQL plugin | Provide `DATABASE_URL` to the API |
| api | `apps/api/Dockerfile` | Runs Alembic then uvicorn |
| web | `apps/web/Dockerfile` | Set `NEXT_PUBLIC_API_URL` to the public API URL at build time |

API environment:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional, default `gpt-4o-mini`)
- `CORS_ORIGINS` (the web origin)
- optional Langfuse keys
- optional `OPENAI_INPUT_USD_PER_MTOK` / `OPENAI_OUTPUT_USD_PER_MTOK`

Web environment:

- `NEXT_PUBLIC_API_URL`

No Redis, workers, or extra datastores.
