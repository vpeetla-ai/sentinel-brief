#!/usr/bin/env sh
# Used by Render Cron Job or manual ops — requires SENTINEL_API_URL env.
set -eu
API="${SENTINEL_API_URL:?Set SENTINEL_API_URL e.g. https://sentinel-brief-api.onrender.com}"
curl -fsS -X POST "${API%/}/runs"
echo ""
curl -fsS "${API%/}/reports?limit=1"
echo ""
