"""Tests for eval gate."""

from app.models.items import RawItem
from app.services.eval_gate import evaluate_brief


def test_eval_passes_with_enough_deltas():
    deltas = [
        RawItem(
            source_id="hn",
            source_label="HN",
            item_id=str(i),
            title=f"Story {i}",
            url=f"https://example.com/{i}",
            summary="AI news",
        )
        for i in range(5)
    ]
    md = "# Sentinel Brief\n\n## Executive summary\n\n- [A](https://a.com)\n- [B](https://b.com)\n- [C](https://c.com)\n"
    result = evaluate_brief(markdown=md, deltas=deltas)
    assert result.passed
    assert result.delta_count == 5


def test_eval_allows_empty_brief():
    md = "# Sentinel Brief\n\n## Executive summary\n\nNo new items.\n"
    result = evaluate_brief(markdown=md, deltas=[])
    assert result.passed
    assert result.delta_count == 0


def test_eval_fails_missing_sections():
    deltas = [
        RawItem(
            source_id="x",
            source_label="X",
            item_id="1",
            title="T",
            url="https://x.com/1",
        )
        for _ in range(4)
    ]
    result = evaluate_brief(markdown="plain text", deltas=deltas)
    assert not result.passed
