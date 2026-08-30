# Secrets

`ai-starter` uses Infisical as the default source of truth for user-managed application secrets.

The goal is that a developer can clone the repository on a new device, authenticate once, and run the project without copying plaintext `.env` files between machines.

## What belongs where

| Kind of value | Source of truth |
| --- | --- |
| `OPENAI_API_KEY`, Langfuse secret keys, third-party API tokens | Infisical |
| Safe defaults and required variable names | `.env.example` in Git |
| Railway-generated `DATABASE_URL` and Railway service references | Railway |
| Vercel project/environment metadata | Vercel |
| Human passwords, passkeys, recovery codes | Password manager |

Do not copy platform-generated values into Infisical solely to force every value into one store. The platform that owns the lifecycle should remain the source of truth for those values.

## Environments

Use separate Infisical environments for the runtime boundaries that matter:

- `dev` — local development
- `preview` — pull-request / preview deployments when needed
- `prod` — production

If the Infisical project uses different environment slugs, map them deliberately. For example, an Infisical `staging` environment can feed Vercel Preview.

Production credentials are not local-development credentials.

## Secret paths

Keep the same path structure across environments:

```text
/common
/api
/web
```

Suggested placement:

```text
/common
  LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY
  LANGFUSE_HOST

/api
  OPENAI_API_KEY

/web
  # only server-side web secrets when the Next.js app actually needs them
```

Public configuration such as `NEXT_PUBLIC_API_URL` is not a secret. Anything prefixed with `NEXT_PUBLIC_` must be safe to expose in browser JavaScript.

## First setup for a real project

This repository is a starter/template, so it intentionally does **not** commit a fixed `.infisical.json`. A fixed project link in the template could make downstream projects point to the wrong vault.

After creating a real project from the starter:

```bash
infisical login
infisical init
```

`infisical init` creates `.infisical.json`. Infisical documents that this file contains project linkage rather than secret values, so the downstream project may commit it after verifying that it points to the correct Infisical project.

Do not add the generated linkage back to the generic `ai-starter` template.

## Local development

Prefer runtime injection instead of a plaintext `.env` file.

From the repository root, run the API with `/common` and `/api` secrets:

```bash
infisical run --env=dev --path=/common --path=/api --project-config-dir=. -- bash -lc 'cd apps/api && uvicorn app.main:app --reload --port 8000'
```

On Windows PowerShell, run from `apps/api` and point back to the repository root:

```powershell
infisical run --env=dev --path=/common --path=/api --project-config-dir=../.. -- uvicorn app.main:app --reload --port 8000
```

For the web app, the current starter needs only public `NEXT_PUBLIC_API_URL`, so no secret injection is required for the default local flow. If server-side web secrets are added later:

```powershell
cd apps/web
infisical run --env=dev --path=/common --path=/web --project-config-dir=../.. -- npm run dev
```

Infisical supports multiple `--path` flags; when the same key exists in more than one requested path, the first path takes precedence. Keep duplicate keys out of multiple folders unless the precedence is intentional.

## `.env` fallback

`.env.example` remains a compatibility/reference file. If Infisical is unavailable for a temporary local demo, copying it to `.env` is acceptable:

```bash
cp .env.example .env
```

Treat `.env` as disposable local state, never as the source of truth. Do not sync it through cloud drives, chat, notes, or Git.

## Vercel and Railway

For user-managed secrets, prefer one-way secret syncs from Infisical into the runtime platform rather than maintaining values manually in two places.

Typical mapping:

```text
Infisical dev      -> local development
Infisical preview  -> Vercel Preview
Infisical prod     -> Vercel Production / Railway production services
```

Railway-owned variables such as a generated `DATABASE_URL` stay in Railway.

## CI

The default CI in this starter is deterministic and does not require production secrets. Keep it that way.

If a future workflow genuinely needs Infisical secrets, use a narrowly scoped machine identity and short-lived workload authentication where supported. Do not give ordinary lint/test/build jobs production secret access.

Live OpenAI evals remain explicit opt-in work and must not silently become a normal PR gate.

## Rules

- Never commit real secret values.
- Never put secrets in issues, PR bodies, screenshots, logs, traces, fixtures, prompts, or docs.
- Keep `.env.example` safe and non-sensitive.
- Never place secrets in `NEXT_PUBLIC_*` variables.
- Give dev, preview, CI, and production separate least-privilege credentials when side effects or cost matter.
- Rotate a credential immediately after exposure. Removing the leaked text is not sufficient.
- Coding agents do not read or modify production secret values unless the user explicitly authorizes that specific production action.
