# Agent Instructions — Sentinel Brief

Read [CONTEXT.md](CONTEXT.md) for shared vocabulary.

## Stack layer

Governed overnight intelligence — adjacent to Content Factory (notify/publish pattern).

## Conventions

- Python 3.11+, FastAPI, Pydantic v2, LangGraph
- `pip install -e ".[dev]"` + `pytest -q` before claiming done
- Email is the **only** irreversible side effect — gateway required in prod
- Sources: allowlist in `config/sources.yaml` — RSS/API first

## When changing

1. Read `docs/ARCHITECTURE.md` and ADR-0001
2. Add adapter + test fixture for new sources
3. Eval gate must pass before email sends
