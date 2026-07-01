# LOOPS — Sentinel Brief

Aligns with [agents-that-run-for-days](https://github.com/vpeetla-ai/vpeetla-ai-skills) harness pattern.

## program.md (human strategy — this doc)

- **Goal:** Daily executive brief from nine AI sources
- **Mutable surface:** `config/sources.yaml`, eval thresholds, summarizer prompt
- **Locked eval:** `evaluate_brief` rules + future golden-eval-registry suite
- **Side effect:** email only — gateway required in prod

## Overnight loop

```text
06:00 UTC cron → POST /runs
  → fetch (read-only)
  → diff vs snapshots
  → write brief
  → eval gate
  → if pass: gateway → email
  → archive report JSON
```

## Keep / discard

| Keep | Discard |
|------|---------|
| Runs with eval pass + archived report | Runs that fail eval (no email) |
| Source adapters with <5% error rate | Adapters breaking feeds 3+ days |
| Gateway audit trail | Fail-open gateway in production |

## Iteration surfaces

1. Add source → new adapter + yaml entry + test fixture
2. Tune `min_delta_items` if too many quiet-day skips
3. Promote template → LLM summarizer when golden eval suite exists
