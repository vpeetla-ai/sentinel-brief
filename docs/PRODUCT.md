# Product — Sentinel Brief

## One-liner

Your **overnight AI radar** — nine curated sources, one governed email, full audit trail.

## Who it's for

| Persona | Job to be done |
|---------|----------------|
| Staff / Principal AI architect | Morning scan of research + industry + HN signal |
| Platform lead | Demo of governed autonomy (LOOPS pattern) |
| Portfolio visitor | See architecture: ingest → eval → gateway email |

## User stories

1. **As an architect**, I want a daily brief in my inbox so I don't manually check nine sites.
2. **As a governance owner**, I want email blocked when eval fails or gateway denies.
3. **As an operator**, I want archived JSON reports and a simple UI to review past runs.

## Sources (v1)

Configured in `config/sources.yaml`:

- Hacker News (top stories)
- HN AI front page (Algolia-filtered)
- arXiv cs.AI
- VentureBeat AI
- MIT Technology Review
- The Information (headlines only — paywalled)
- Paper Digest
- The Batch (Andrew Ng / DeepLearning.AI)
- Towards Data Science (Medium)

## Success metrics

| Metric | Target |
|--------|--------|
| Run completion | >95% nightly |
| Eval pass rate | >80% on active news days |
| Gateway block audit | 100% logged |
| Source fetch errors | <2 per run (degraded OK) |

## Non-goals (v1)

- Paywall content extraction
- Multi-tenant / team inboxes
- Real-time streaming
- Social publish (LinkedIn/X) — that's Content Factory

## Roadmap

| Phase | Deliverable |
|-------|-------------|
| **MVP (now)** | Adapters, graph, eval, gateway email, API, demo UI |
| **v0.2** | LLM synthesis + golden eval suite |
| **v0.3** | Dedup, source health dashboard, Render cron |
| **v1.0** | HITL approval queue integration with AegisLoop |

## Competitive framing

Unlike generic "AI news aggregators," Sentinel Brief is a **portfolio proof** of:

- Allowlisted ingest
- Snapshot diffs (signal over noise)
- Eval-gated output
- Gateway-governed side effects

## Demo

- API: `/health`, `POST /runs`, `GET /reports`
- Static UI: `demo/index.html` — architecture tabs + latest reports
