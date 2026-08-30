# Architecture

One vertical slice:

```
Next.js form
  → FastAPI POST /api/v1/analyze
  → validate
  → wrap untrusted text (ai-core)
  → OpenAI structured completion (ai-core)
  → persist metadata in PostgreSQL
  → show result in the UI
```

`ai-core` owns provider, retry, structured output, redaction, and optional Langfuse. This repo does not reimplement those.

`agent-eval-harness` owns scoring and the regression gate. This repo only adds a suite and a thin target.
