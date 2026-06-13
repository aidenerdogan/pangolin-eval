from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pangolin_eval.models import ModelTarget
from pangolin_eval.pricing import (
    PRICING_CATALOG_SCHEMA_VERSION,
    apply_pricing_catalog,
    load_pricing_catalog,
)


def catalog() -> dict[str, object]:
    return {
        "schema_version": PRICING_CATALOG_SCHEMA_VERSION,
        "models": [
            {
                "id": "mock-model",
                "input_price_per_1m": 1.0,
                "output_price_per_1m": 2.0,
                "source": "test_catalog",
                "source_url": "https://example.test/pricing",
                "last_updated": "2026-06-13",
            }
        ],
    }


class PricingTest(unittest.TestCase):
    def test_load_pricing_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pricing.json"
            path.write_text(json.dumps(catalog()), encoding="utf-8")

            loaded = load_pricing_catalog(path)

        self.assertEqual(loaded["schema_version"], PRICING_CATALOG_SCHEMA_VERSION)

    def test_apply_pricing_catalog_updates_model_prices_and_provenance(self) -> None:
        models = [
            ModelTarget(
                id="mock-model",
                provider="mock",
                input_price_per_1m=0.1,
                output_price_per_1m=0.2,
            )
        ]

        updated = apply_pricing_catalog(models, catalog())

        self.assertEqual(updated[0].input_price_per_1m, 1.0)
        self.assertEqual(updated[0].output_price_per_1m, 2.0)
        self.assertEqual(updated[0].pricing_source, "test_catalog")
        self.assertEqual(updated[0].pricing_updated_at, "2026-06-13")

    def test_apply_pricing_catalog_respects_manual_override(self) -> None:
        models = [
            ModelTarget(
                id="mock-model",
                provider="mock",
                input_price_per_1m=0.1,
                output_price_per_1m=0.2,
                extra={"price_override": True},
            )
        ]

        updated = apply_pricing_catalog(models, catalog())

        self.assertEqual(updated[0].input_price_per_1m, 0.1)
        self.assertEqual(updated[0].pricing_source, "manual_override")


if __name__ == "__main__":
    unittest.main()
