"""Tests for summarizer."""

from app.models.items import RawItem
from app.services.summarizer import summarize_brief


def test_summarize_includes_citations():
    deltas = [
        RawItem(
            source_id="arxiv",
            source_label="arXiv cs.AI",
            item_id="1",
            title="Paper One",
            url="https://arxiv.org/abs/1",
            summary="Abstract",
        )
    ]
    md = summarize_brief(deltas=deltas, run_id="r1")
    assert "Paper One" in md
    assert "https://arxiv.org/abs/1" in md
    assert "## Executive summary" in md
