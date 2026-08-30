# Deployment

Default deployment split for projects created from `ai-starter`:

- `apps/web` (Next.js) -> Vercel
- `apps/api` (FastAPI) -> Railway
- PostgreSQL -> Railway managed PostgreSQL
- GitHub -> code source of truth and pull-request boundary
- Infisical -> source of truth for user-managed application secrets

## Flow

```text
feature branch
  -> GitHub CI
  -> Vercel Preview (web)
  -> review
  -> human merge to main
  -> Vercel/Railway production deployment
  -> health + smoke verification
```

Coding agents do not merge, promote, or deploy production by themselves.

## Environments

Start with:

- local `dev`
- pull-request `preview`
- `prod`

Do not add a permanent staging environment until a real integration, migration, customer acceptance, or production-like test requires one.

## Vercel

Create a Vercel project for `apps/web` and set its root directory accordingly. Use Preview Deployments for pull requests and Production for `main`.

`NEXT_PUBLIC_API_URL` is a build-time/public value and must point at the API appropriate for the deployment environment. Do not put secrets in `NEXT_PUBLIC_*` variables.

When user-managed server-side web secrets are added later, prefer syncing them from the matching Infisical environment instead of maintaining duplicate values manually.

## Railway

See `docs/RAILWAY.md` for the current API/PostgreSQL service details.

Keep Railway-generated values, such as its managed database connection value, owned by Railway. User-managed credentials such as `OPENAI_API_KEY` should come from Infisical where practical.

Use `/health` for liveness and `/ready` for database readiness. Migration behavior remains explicit in the API deployment path.

## Production safety

The current analyze endpoint is unauthenticated and can spend the configured OpenAI key. Do not expose it publicly as a customer-facing production API until access control or a gateway is in place.

After production deployment, verify at minimum:

1. web page loads;
2. API `/health` returns success;
3. API `/ready` returns success;
4. the smallest critical end-to-end request succeeds under the intended access controls.

## Secrets

See `docs/SECRETS.md`.

Do not commit deployment credentials, Vercel/Railway tokens, API keys, or generated plaintext `.env` files.
