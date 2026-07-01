"""Brief quality eval gate — citations, min deltas, structure."""

from __future__ import annotations

import re

from app.core.config import get_settings
from app.models.items import BriefEvalResult, RawItem


def evaluate_brief(*, markdown: str, deltas: list[RawItem]) -> BriefEvalResult:
    settings = get_settings()
    reasons: list[str] = []
    citation_count = len(re.findall(r"\]\(https?://", markdown))
    delta_count = len(deltas)

    if delta_count < settings.min_delta_items:
        reasons.append(f"Fewer than {settings.min_delta_items} new items ({delta_count})")

    if citation_count < min(3, max(1, delta_count)):
        reasons.append(f"Insufficient citations ({citation_count})")

    if "# Sentinel Brief" not in markdown:
        reasons.append("Missing brief header")

    if "## Executive summary" not in markdown:
        reasons.append("Missing executive summary section")

    # Empty run is valid — pass with note
    if delta_count == 0:
        return BriefEvalResult(
            passed=True,
            score=1.0,
            reasons=["No deltas — empty brief allowed"],
            citation_count=citation_count,
            delta_count=0,
        )

    passed = len(reasons) == 0
    score = 1.0 if passed else max(0.0, 1.0 - 0.25 * len(reasons))
    return BriefEvalResult(
        passed=passed,
        score=score,
        reasons=reasons,
        citation_count=citation_count,
        delta_count=delta_count,
    )
