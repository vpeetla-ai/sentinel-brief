# Deploy — Sentinel Brief

## Split

| Layer | Host | Folder |
|-------|------|--------|
| API | Render | repo root (`render.yaml`) |
| Demo UI | Vercel | `demo/` |

## Render (API)

1. Connect [vpeetla-ai/sentinel-brief](https://github.com/vpeetla-ai/sentinel-brief) in Render dashboard.
2. Use existing `render.yaml` — **plan: free**.
3. Set env vars:

| Variable | Required | Notes |
|----------|----------|-------|
| `BRIEF_RECIPIENT_EMAIL` | For real email | Your inbox |
| `RESEND_API_KEY` | For real email | Resend dashboard |
| `AEGISAI_API_BASE_URL` | Prod governance | AegisAI API URL |
| `AEGISAI_GATEWAY_ENABLED` | Prod | `true` |
| `AEGISAI_GATEWAY_FAIL_OPEN` | Prod | `false` |

4. Health check: `GET /health`

```bash
curl https://YOUR-SERVICE.onrender.com/health
curl -X POST https://YOUR-SERVICE.onrender.com/runs
```

### Overnight cron (pick one)

**A — GitHub Actions** (`.github/workflows/nightly.yml`): set repo secret `SENTINEL_API_URL` to your Render URL.

**B — Render cron job**: schedule `POST /runs` daily at 06:00 UTC.

**C — Manual**: `curl -X POST .../runs`

## Vercel (demo UI)

```bash
cd demo
vercel --prod
```

In Vercel project settings, add env `SENTINEL_API` = your Render API base URL (no trailing slash).

The demo reads `window.SENTINEL_API` or builds it from `config.js` if present.

## Cold start

Render free tier sleeps after ~15 min idle. First cron hit may take 30–60s to wake.

## Local

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --app-dir backend
```
