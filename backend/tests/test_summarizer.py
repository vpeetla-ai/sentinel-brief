"""Tests for summarizer — template fallback and real LLM executive summary."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.models.items import RawItem
from app.services.summarizer import summarize_brief


def _item(title="Paper One", label="arXiv cs.AI"):
    return RawItem(
        source_id="arxiv",
        source_label=label,
        item_id="1",
        title=title,
        url="https://arxiv.org/abs/1",
        summary="Abstract",
    )


async def test_summarize_includes_citations():
    md = await summarize_brief(deltas=[_item()], run_id="r1")
    assert "Paper One" in md
    assert "https://arxiv.org/abs/1" in md
    assert "## Executive summary" in md


async def test_summarize_falls_back_to_template_when_no_llm_key_configured():
    settings = MagicMock()
    settings.groq_api_key = None
    settings.openai_api_key = None
    with patch("app.services.summarizer.get_settings", return_value=settings):
        md = await summarize_brief(deltas=[_item()], run_id="r1")
    assert "Overnight scan across" in md


async def test_summarize_uses_real_llm_when_groq_key_configured():
    settings = MagicMock()
    settings.groq_api_key = "gsk_test"
    settings.openai_api_key = None
    mock_response = MagicMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {"choices": [{"message": {"content": "A real synthesized summary."}}]}

    with patch("app.services.summarizer.get_settings", return_value=settings):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            md = await summarize_brief(deltas=[_item()], run_id="r1")

    assert "A real synthesized summary." in md
    assert "Overnight scan across" not in md


async def test_summarize_falls_back_to_template_when_llm_call_fails():
    settings = MagicMock()
    settings.groq_api_key = "gsk_test"
    settings.openai_api_key = None

    with patch("app.services.summarizer.get_settings", return_value=settings):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=RuntimeError("boom"))
            md = await summarize_brief(deltas=[_item()], run_id="r1")

    assert "Overnight scan across" in md


async def test_summarize_no_deltas_short_circuits_before_llm_call():
    md = await summarize_brief(deltas=[], run_id="r1")
    assert "No new items" in md
