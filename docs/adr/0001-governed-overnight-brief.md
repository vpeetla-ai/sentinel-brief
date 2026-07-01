# ADR-0001: Governed overnight brief (Sentinel Brief)

## Status

Accepted — 2026-07-01

## Context

We need an **autonomous system** that runs overnight: scrape/fetch → summarize → email, without human intervention per run. The vpeetla-ai stack separates **orchestration** (VAP/LangGraph) from **governance** (AegisAI). Email is an irreversible side effect.

User-specified sources span public APIs, RSS feeds, and paywalled journalism (The Information).

## Decision

1. **Repo:** `sentinel-brief` — standalone governed reporter
2. **Pipeline:** LangGraph linear graph with six nodes (fetch → diff → brief → eval → gateway+email → archive)
3. **Ingest:** Allowlisted adapters in `config/sources.yaml`; **RSS/API first**, no Playwright in MVP
4. **Autonomy boundary:** Inner loop (fetch, diff, summarize, eval) runs unattended; **only email** crosses the governance gateway
5. **Paywalled sources:** `rss_partial` adapter — headlines only, metadata `paywalled: true`; no bypass
6. **Eval gate:** In-process rules (min deltas, citations, structure); future golden-eval-registry suite
7. **Persistence:** JSON snapshots + JSON reports (MVP); SQLite considered for v0.2

## Consequences

### Positive

- Clear architecture story for portfolio
- Matches org patterns (gateway, eval, LangGraph)
- Testable without network (mock adapters)
- Honest handling of paywalled content

### Negative

- Template brief is less compelling than LLM narrative
- RSS feeds can break or rate-limit
- No cross-source dedup in MVP
- First run always surfaces many "new" items (cold snapshot)

## Alternatives rejected

| Alternative | Why not |
|-------------|---------|
| Email without gateway | Violates org governance story |
| Playwright scrape all sources | Fragile, ToS risk, ops cost |
| Human approval every run | Defeats overnight autonomy |
| Single monolithic cron script | No eval, no audit trail, hard to test |

## Tradeoffs summary

```text
Autonomy ◄────────────────────────────► Control
         eval gate          gateway email
         (inner loop)       (outer loop)
```

## References

- ai-content-factory gateway pattern
- loop-engine-agent-platform LOOPS.md
- golden-eval-registry (planned consumer)
