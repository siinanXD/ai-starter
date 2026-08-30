"use client";

import { FormEvent, useState } from "react";

import { analyzeText, type AnalyzeResult } from "@/lib/api";

export function AnalyzeForm() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await analyzeText(text));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analyze failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <h1>Analyze</h1>
      <p className="lede">
        Submit a short customer message. The API classifies it with OpenAI through
        ai-core and stores metadata only.
      </p>
      <form onSubmit={onSubmit}>
        <label htmlFor="text">Customer message</label>
        <textarea
          id="text"
          name="text"
          rows={6}
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={4000}
          required
        />
        <button type="submit" disabled={loading || text.trim().length === 0}>
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>
      {error ? <p className="error" role="alert">{error}</p> : null}
      {result ? (
        <article className="card">
          <p>
            <strong>Summary</strong>
            {result.summary}
          </p>
          <p>
            <strong>Category</strong>
            {result.category}
          </p>
          <p>
            <strong>Confidence</strong>
            {result.confidence}
          </p>
          <p>
            <strong>Suggested action</strong>
            {result.suggested_action}
          </p>
          <dl className="meta">
            <div>
              <dt>Model</dt>
              <dd>{result.model}</dd>
            </div>
            <div>
              <dt>Latency</dt>
              <dd>{result.latency_ms} ms</dd>
            </div>
            <div>
              <dt>Tokens</dt>
              <dd>
                {result.input_tokens ?? "—"} in / {result.output_tokens ?? "—"} out
              </dd>
            </div>
            <div>
              <dt>Estimated cost</dt>
              <dd>
                {result.estimated_cost_usd == null
                  ? "unknown"
                  : `$${result.estimated_cost_usd.toFixed(6)}`}
              </dd>
            </div>
          </dl>
        </article>
      ) : null}
    </main>
  );
}
