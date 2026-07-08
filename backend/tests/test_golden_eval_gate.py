"""Golden eval registry gate — sentinel_brief_gate_v1."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from app.models.items import RawItem
from app.services.eval_gate import evaluate_brief

try:
    from golden_eval_registry.runner import score_suite
    from golden_eval_registry.schema import parse_manifest
    from golden_eval_registry.validate import load_jsonl

    GOLDEN_EVAL_REGISTRY_AVAILABLE = True
except ImportError:
    GOLDEN_EVAL_REGISTRY_AVAILABLE = False

REGISTRY_PATH = Path(os.getenv("GOLDEN_EVAL_REGISTRY_PATH", "../golden-eval-registry")).resolve()
SUITE_DIR = REGISTRY_PATH / "suites" / "sentinel_brief_gate_v1"


@unittest.skipUnless(
    GOLDEN_EVAL_REGISTRY_AVAILABLE and SUITE_DIR.exists(),
    "golden-eval-registry not available — set GOLDEN_EVAL_REGISTRY_PATH or run in CI",
)
class SentinelBriefGoldenEvalGateTests(unittest.TestCase):
    def test_sentinel_brief_gate_v1_suite_passes(self) -> None:
        manifest = parse_manifest(SUITE_DIR / "manifest.json")
        cases = load_jsonl(manifest.cases_path)

        actual_by_id: dict[str, dict] = {}
        for case in cases:
            payload = case["input"]
            delta_count = int(payload.get("delta_count", 0))
            deltas = [
                RawItem(
                    source_id="test",
                    source_label="test",
                    item_id=f"item-{i}",
                    title=f"item-{i}",
                    url=f"https://example.com/{i}",
                    summary="summary",
                )
                for i in range(delta_count)
            ]
            result = evaluate_brief(markdown=payload["markdown"], deltas=deltas)
            actual_by_id[str(case["id"])] = {
                "passed": result.passed,
                "citation_count": result.citation_count,
                "score": result.score,
            }

        suite_result = score_suite(manifest, cases, actual_by_id)
        failures = "\n".join(f"{f.case_id}: {f.detail}" for f in suite_result.failures)
        self.assertTrue(suite_result.passed, f"golden eval regressions:\n{failures}")


if __name__ == "__main__":
    unittest.main()
