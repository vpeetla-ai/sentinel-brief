"""Email delivery — Resend API with dry-run fallback."""

from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_brief_email(*, subject: str, html_body: str, text_body: str) -> dict:
    settings = get_settings()
    recipient = settings.brief_recipient_email
    if not recipient:
        logger.info("No BRIEF_RECIPIENT_EMAIL — dry run")
        return {"status": "dry_run", "recipient": None}

    if not settings.resend_api_key:
        logger.info("No RESEND_API_KEY — logging only")
        return {"status": "logged", "recipient": recipient}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.brief_from_email,
                "to": [recipient],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return {"status": "sent", "recipient": recipient, "id": data.get("id")}
