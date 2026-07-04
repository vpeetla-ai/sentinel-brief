# Deploy — Sentinel Brief

Step-by-step for **vpeetla-ai@gmail.com** daily brief.

## How it works (important)

```text
CRON (schedule)  →  POST /runs  →  fetch + diff + brief + eval
                                              ↓
                                    if eval passes
                                              ↓
                                    Resend email → vpeetla.ai@gmail.com
                                              ↓
                                    JSON report archived (GET /reports)
```

- **Cron triggers the run** — email does not trigger anything.
- **Email is the output** after eval pass (and gateway allow if enabled).
- **Reports** are always archived on the API even when email is skipped.

---

## Render: Blueprint vs Web Service

| Approach | When to use | Sentinel Brief |
|----------|-------------|----------------|
| **Blueprint** | Repo has `render.yaml` at root | **Use this** |
| **Web Service** | Manual one-off service, no yaml | Only if Blueprint fails |

### Recommended: New Blueprint

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect GitHub org **vpeetla-ai** → repo **sentinel-brief**
3. Render reads [`render.yaml`](../render.yaml) and creates:
   - **One Web Service:** `sentinel-brief-api` (Docker, free plan)
4. Click **Apply** — first deploy takes ~5–10 min
5. Copy the service URL, e.g. `https://sentinel-brief-api.onrender.com`

### If you already created a manual Web Service

You can keep it — just ensure:

- **Runtime:** Docker  
- **Dockerfile path:** `./backend/Dockerfile`  
- **Docker context:** `.` (repo root)  
- **Health check path:** `/health`  
- **Plan:** Free  

Blueprint is still easier for future yaml updates.

---

## Render env vars (Dashboard → sentinel-brief-api → Environment)

Set these **in Render only** (not in git):

| Variable | Value | Required |
|----------|-------|----------|
| `BRIEF_RECIPIENT_EMAIL` | `vpeetla.ai@gmail.com` | Yes (for inbox) |
| `RESEND_API_KEY` | `re_...` from Resend | Yes (for inbox) |
| `BRIEF_FROM_EMAIL` | Verified sender in Resend | Yes |
| `AEGISAI_GATEWAY_ENABLED` | `false` (MVP) | No |
| `AEGISAI_GATEWAY_FAIL_OPEN` | `true` (MVP) | No |
| `MIN_DELTA_ITEMS` | `3` (default) | No |
| `SENTINEL_API_KEY` | Random secret | **Yes before treating this as production** — without it, `POST /runs` has no auth at all (see [ADR-0002](adr/0002-runs-auth-and-llm-synthesis.md)); set the same value as the `SENTINEL_API_KEY` GitHub Actions secret so the nightly cron keeps working |
| `GROQ_API_KEY` | `gsk_...` from Groq | No — real LLM executive summary; template fallback used when unset |

### Observability (optional — Langfuse Cloud)

| Variable | Value | Required |
|----------|-------|----------|
| `LANGFUSE_PUBLIC_KEY` | `pk-lf-...` from Langfuse project | No |
| `LANGFUSE_SECRET_KEY` | `sk-lf-...` | No |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | No (default) |
| `LANGFUSE_ENABLED` | `true` | No |

1. [cloud.langfuse.com](https://cloud.langfuse.com) → create project `sentinel-brief`
2. Settings → API Keys → copy public + secret keys into Render env
3. Trigger `POST /runs` → Langfuse → **Traces** → filter by project

`render.yaml` already declares `LANGFUSE_*` keys — fill values in the dashboard after Blueprint apply.

### Verify API after deploy

```bash
curl https://sentinel-brief-api.onrender.com/health
# {"status":"ok","service":"sentinel-brief"}

curl -X POST https://sentinel-brief-api.onrender.com/runs
# First run may take 30–60s (cold start + fetching 9 sources)

curl https://sentinel-brief-api.onrender.com/reports?limit=3
```

---

## Email setup (Resend)

1. Sign up at [resend.com](https://resend.com)
2. **API Keys** → Create → copy `re_...`
3. Paste into Render env `RESEND_API_KEY`
4. **Sender address:**
   - **Quick test:** use `onboarding@resend.dev` as `BRIEF_FROM_EMAIL` (Resend sandbox — may only deliver to your Resend account email until domain verified)
   - **Production:** add and verify domain `vpeetla.ai` (or your sending domain) in Resend → use e.g. `sentinel@vpeetla.ai`
5. Set `BRIEF_RECIPIENT_EMAIL=vpeetla.ai@gmail.com` in Render
6. Trigger a test run: `curl -X POST https://YOUR-API.onrender.com/runs`
7. Check Gmail inbox + spam; check Render logs if no mail

**No email config in code** — only env vars. Without `RESEND_API_KEY`, runs still work but email status is `dry_run` / `logged`.

---

## Overnight cron (pick one)

### Option A — GitHub Actions (recommended, free)

Already in [`.github/workflows/nightly.yml`](../.github/workflows/nightly.yml) — runs **06:00 UTC** daily.

**One-time setup:**

1. GitHub → **vpeetla-ai/sentinel-brief** → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret:**
   - Name: `SENTINEL_API_URL`
   - Value: `https://sentinel-brief-api.onrender.com` (your Render URL, **no** trailing slash)
3. **Actions** tab → **Nightly brief** → **Run workflow** (manual test)

The workflow:

```bash
curl -X POST $SENTINEL_API_URL/runs
curl $SENTINEL_API_URL/reports?limit=1
```

If secret is missing, workflow skips gracefully (no failure).

### Option B — Render Cron Job (optional second service)

Render **Cron Job** is a separate service type (not in current `render.yaml`). To add:

1. **New** → **Cron Job**
2. Schedule: `0 6 * * *` (06:00 UTC)
3. Command (shell):

```bash
curl -fsS -X POST "https://sentinel-brief-api.onrender.com/runs"
```

4. Use a **curl** or **ubuntu** runtime image, or add a tiny `scripts/cron_trigger.sh` in repo

GitHub Actions is simpler because URL lives in one secret and no extra Render service.

### Option C — Manual

```bash
curl -X POST https://sentinel-brief-api.onrender.com/runs
```

---

## Vercel (demo UI)

**Live demo (vpeetla-ai team):** [sentinel-brief-ruddy.vercel.app](https://sentinel-brief-ruddy.vercel.app)

> `sentinel-brief.vercel.app` is registered to a **different** Vercel project (unrelated OSINT app). Use the team URL above or reclaim the domain in Vercel → Domains.

1. [Vercel Dashboard](https://vercel.com) → **Add New** → **Project**
2. Import **vpeetla-ai/sentinel-brief**
3. **Root Directory:** leave as repo root — [`vercel.json`](../vercel.json) sets `outputDirectory: demo`
4. Framework: **Other** (static)
5. Deploy

**Wire API to demo** — [`demo/config.js`](../demo/config.js):

```javascript
window.SENTINEL_API = "https://sentinel-brief-api.onrender.com";
```

The **Reports** tab loads live runs from Render (CORS enabled).

---

## Checklist

| Step | Done? |
|------|-------|
| Render Blueprint applied (`sentinel-brief-api` live) | ☐ |
| `GET /health` returns ok | ☐ |
| `BRIEF_RECIPIENT_EMAIL=vpeetla.ai@gmail.com` in Render | ☐ |
| `RESEND_API_KEY` + verified `BRIEF_FROM_EMAIL` in Render | ☐ |
| Test `POST /runs` — report in `/reports` | ☐ |
| Test email received in Gmail | ☐ |
| GitHub secret `SENTINEL_API_URL` set | ☐ |
| Nightly workflow run once (manual dispatch) | ☐ |
| Vercel demo deployed + `config.js` API URL | ☐ |

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `POST /runs` timeout | Render cold start — retry after 60s |
| No email, status `dry_run` | Missing `RESEND_API_KEY` or recipient |
| No email, status `skipped`, eval failed | Quiet day — fewer than `MIN_DELTA_ITEMS` new items |
| Source errors in report | RSS feed down — run still completes, partial data |
| 502 on first request | Free tier waking up — normal |

---

## Local dev

```bash
cp .env.example .env   # fill RESEND_API_KEY locally if testing email
pip install -e ".[dev]"
pytest -q
uvicorn app.main:app --reload --app-dir backend
curl -X POST http://localhost:8000/runs
```

See also [`.env.example`](../.env.example).
