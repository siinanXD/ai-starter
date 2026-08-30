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

PostgreSQL stores metadata only: hash, category, confidence, model, tokens, cost, latency. Model free-text (`summary`, `suggested_action`) is returned to the client and is not persisted.

`agent-eval-harness` owns scoring and the regression gate. The deterministic target calls `analyze_text` with a fake provider.
