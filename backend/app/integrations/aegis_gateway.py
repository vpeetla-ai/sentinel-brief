"""AegisAI governance gateway — authorize email side effects."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GatewayAuthz:
    allowed: bool
    requires_approval: bool
    blocked: bool
    decision: str
    reason: str
    case_id: str | None = None
    raw: dict[str, Any] | None = None


def gateway_enabled() -> bool:
    settings = get_settings()
    return bool(settings.aegisai_api_base_url and settings.aegisai_gateway_enabled)


async def authorize_email(*, run_id: str, recipient: str) -> GatewayAuthz:
    settings = get_settings()
    if not gateway_enabled():
        return GatewayAuthz(
            allowed=True,
            requires_approval=False,
            blocked=False,
            decision="gateway_disabled",
            reason="AegisAI gateway not configured — dev mode allow",
        )

    url = f"{settings.aegisai_api_base_url.rstrip('/')}/gateway/authorize"
    payload = {
        "tool_name": "email.send",
        "action_type": "notify",
        "target_system": "resend",
        "case_id": run_id,
        "metadata": {"recipient": recipient, "brief_run": run_id},
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Gateway authorize failed: %s", exc)
        if settings.aegisai_gateway_fail_open:
            return GatewayAuthz(
                allowed=True,
                requires_approval=False,
                blocked=False,
                decision="fail_open",
                reason=str(exc),
            )
        return GatewayAuthz(
            allowed=False,
            requires_approval=False,
            blocked=True,
            decision="fail_closed",
            reason=str(exc),
        )

    decision = data.get("decision", "unknown")
    allowed = decision in {"allow", "approved"}
    blocked = decision in {"deny", "blocked"}
    requires_approval = decision == "pending_approval"
    return GatewayAuthz(
        allowed=allowed and not blocked,
        requires_approval=requires_approval,
        blocked=blocked,
        decision=decision,
        reason=data.get("reason", ""),
        case_id=data.get("case_id"),
        raw=data,
    )
