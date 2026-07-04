# ADR-0002: API-Key Gate on POST /runs, Real LLM Executive Summary

## Status

Accepted — 2026-07-03

## Context

ADR-0001 shipped two known MVP gaps: `POST /runs` had zero authentication despite triggering
an LLM call and a real email send on every hit (config already declared `openai_api_key` /
`groq_api_key` but `summarize_brief` never read them — the executive summary was 100%
templated regardless of whether a key was configured). Both the nightly GitHub Actions cron
and the public demo UI's "Run brief now" button call `POST /runs` directly with no credential.
Left as-is, anyone who found the Render URL could trigger unlimited runs, burning LLM/Resend
quota and spamming the recipient inbox.

## Decision

1. **`SENTINEL_API_KEY` gate on `POST /runs` only.** `GET /reports` and `GET /reports/{id}`
   stay open — the archive is meant to be publicly browsable (`docs/PRODUCT.md`: "portfolio
   proof" positioning). Enforced only when the env var is set, so local dev/demo default stays
   open. The demo UI's "Run brief now" button gained an optional password-type input that
   sends whatever the visitor types as `X-API-Key` — never persisted, never baked into the
   static page. The nightly cron workflow now sends a matching `SENTINEL_API_KEY` GitHub
   Actions secret.
2. **Real LLM executive summary**, Groq preferred (cheap/fast) then OpenAI, both called via
   plain `httpx` against their OpenAI-compatible `/chat/completions` endpoint (no new SDK
   dependency). Falls back to the original deterministic template on missing key *or* any
   failure (timeout, non-2xx, malformed response) — a summary is never allowed to block a run
   or crash it; degrade instead of fail.

## Consequences

### Positive
- `POST /runs` can no longer be freely spammed once `SENTINEL_API_KEY` is set on Render.
- The brief's executive summary is now real synthesis when a key is configured, closing the
  gap ADR-0001 explicitly called out as "less compelling than LLM narrative."
- Fallback-on-failure means an LLM outage degrades quality, not availability.

### Negative
- `SENTINEL_API_KEY` must be set (and matched in the GitHub Actions secret + anyone using the
  demo's run-now button) or the deployment remains as open as before — this is a deploy-time
  action item, not automatic.
- Slightly higher latency/cost per run when an LLM key is configured (~1 extra network call,
  20s timeout).
- Persistent (non-ephemeral) report storage remains unresolved — Render's free-tier disk still
  resets on redeploy. Deferred; it's a separate storage-provider decision (S3/R2/etc.), not a
  same-pass code fix.

## References
- `backend/app/main.py::_require_api_key`
- `backend/app/services/summarizer.py::_llm_executive_summary`
- Same pattern applied org-wide: [loop-engine-agent-platform ADR-002](https://github.com/vpeetla-ai/loop-engine-agent-platform/blob/main/docs/ADR-002-repo-fix-auth-and-isolation.md), [ai-architecture-portfolio ADR-008](https://github.com/vpeetla-ai/ai-architecture-portfolio/blob/main/adr/ADR-008-real-publish-scope-and-invite-gating.md)
