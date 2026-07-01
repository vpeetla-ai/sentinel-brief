# Sentinel Brief

[![CI](https://github.com/vpeetla-ai/sentinel-brief/actions/workflows/ci.yml/badge.svg)](https://github.com/vpeetla-ai/sentinel-brief/actions/workflows/ci.yml)

**Governed overnight AI intelligence reporter** — allowlisted sources → snapshot diff → executive brief → eval gate → gateway-authorized email → archived reports.

## Problem

Staying current on AI research, industry news, and community signal across nine+ sources is manual and noisy. You want a **daily executive brief** that runs while you sleep — but **email is a side effect** and must stay governed.

## Architecture (60s)

```mermaid
flowchart TB
  subgraph schedule [Schedule]
    CRON[Render cron / POST /runs]
  end

  subgraph ingest [Ingest — read-only]
    SRC[Allowlisted adapters]
    SRC --> HN[HN Firebase + Algolia AI]
    SRC --> ARX[arXiv cs.AI Atom]
    SRC --> RSS[RSS feeds]
  end

  subgraph pipeline [LangGraph pipeline]
    F[fetch_sources]
    D[diff_items]
    S[write_brief]
    E[run_eval]
    G[gateway_and_email]
    A[archive_report]
    F --> D --> S --> E --> G --> A
  end

  subgraph store [Persistence]
    SNAP[(snapshots/)]
    REP[(reports/)]
  end

  subgraph govern [Governance]
    EVAL[Eval gate]
    GW[AegisAI gateway]
    MAIL[Resend email]
  end

  CRON --> F
  ingest --> F
  D <--> SNAP
  A --> REP
  E --> EVAL
  G --> GW --> MAIL
```

## Status

| Area | Status | Notes |
|------|--------|-------|
| Source adapters (9 allowlisted) | ✅ MVP | RSS/API first; paywalled = headline only |
| Snapshot + delta detection | ✅ | JSON per source |
| LangGraph pipeline | ✅ | fetch → diff → summarize → eval → email → archive |
| Eval gate | ✅ | Min deltas, citations, structure |
| AegisAI gateway on email | ✅ | Fail-open dev / fail-closed prod |
| Resend email | ✅ | Dry-run without keys |
| FastAPI + report archive | ✅ | `GET /reports`, `GET /reports/{id}` |
| Demo UI | ✅ | Static `demo/` — architecture + report viewer |
| Render deploy | 🟡 | `render.yaml` ready; cron manual |
| LLM summarization | 🟡 | Template brief MVP; LLM hook planned |
| Playwright scrape | ⬜ | Deferred — RSS/API per ADR-0001 |

## Quick start

```bash
cd sentinel-brief
pip install -e ".[dev]"
pytest -q
uvicorn app.main:app --reload --app-dir backend
# Trigger a run
curl -X POST http://localhost:8000/runs
```

Env (optional):

```bash
BRIEF_RECIPIENT_EMAIL=you@example.com
RESEND_API_KEY=re_...
AEGISAI_API_BASE_URL=https://your-aegis-api
AEGISAI_GATEWAY_ENABLED=true
```

## Sources (allowlisted)

| Source | Adapter | Access |
|--------|---------|--------|
| Hacker News (top) | Firebase API | Public |
| HN AI front page | Algolia HN search | Public |
| arXiv cs.AI | Atom API | Public |
| VentureBeat AI | RSS | Public |
| MIT Technology Review | RSS | Public |
| The Information | RSS partial | Paywalled headlines |
| Paper Digest | RSS | Public |
| The Batch (DeepLearning.AI) | RSS | Public |
| Towards Data Science | Medium RSS | Public (ToS) |

Configure in [`config/sources.yaml`](config/sources.yaml).

## Docs

- [Architecture](docs/ARCHITECTURE.md) — layers, decisions, tradeoffs
- [Product](docs/PRODUCT.md) — who, jobs-to-be-done, roadmap
- [ADR-0001](docs/adr/0001-governed-overnight-brief.md) — governed autonomy pattern
- [LOOPS](docs/LOOPS.md) — overnight harness alignment

## Stack fit (vpeetla-ai)

| Layer | Integration |
|-------|-------------|
| Orchestration | LangGraph `StateGraph` |
| Governance | AegisAI gateway on `email.send` |
| Evaluation | In-repo eval gate + golden-eval-registry (planned suite) |
| Observability | Structured report JSON; Langfuse hook planned |
| Deploy | Render API + Vercel static demo |

Part of the [vpeetla-ai](https://github.com/vpeetla-ai) governed agent portfolio.
