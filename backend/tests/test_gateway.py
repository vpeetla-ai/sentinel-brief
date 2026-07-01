"""Tests for gateway authorization."""

import pytest

from app.integrations.aegis_gateway import authorize_email


@pytest.mark.asyncio
async def test_gateway_disabled_allows():
    authz = await authorize_email(run_id="run-1", recipient="a@b.com")
    assert authz.allowed
    assert authz.decision == "gateway_disabled"
