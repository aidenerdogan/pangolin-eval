from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from pangolin_eval.models import ModelTarget

PRICING_CATALOG_SCHEMA_VERSION = "pangolin-eval.pricing.v1"


def load_pricing_catalog(path: str | Path) -> dict[str, Any]:
    catalog_path = Path(path)
    with catalog_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate_pricing_catalog(data)
    return data


def validate_pricing_catalog(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("Pricing catalog must be a JSON object.")
    if data.get("schema_version") != PRICING_CATALOG_SCHEMA_VERSION:
        raise ValueError(
            "Pricing catalog schema_version must be "
            f"'{PRICING_CATALOG_SCHEMA_VERSION}'."
        )
    models = data.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("Pricing catalog must include a non-empty 'models' list.")
    for index, entry in enumerate(models, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Pricing catalog model {index} must be an object.")
        for field in ["id", "input_price_per_1m", "output_price_per_1m", "source"]:
            if field not in entry:
                raise ValueError(f"Pricing catalog model {index} is missing '{field}'.")
        if not isinstance(entry["id"], str) or not entry["id"].strip():
            raise ValueError(f"Pricing catalog model {index} field 'id' must be a string.")
        _require_non_negative_number(entry, "input_price_per_1m", index)
        _require_non_negative_number(entry, "output_price_per_1m", index)
        for optional in ["source", "source_url", "last_updated"]:
            if optional in entry and not isinstance(entry[optional], str):
                raise ValueError(
                    f"Pricing catalog model {index} field '{optional}' must be a string."
                )


def apply_pricing_catalog(
    models: list[ModelTarget],
    catalog: dict[str, Any],
) -> list[ModelTarget]:
    entries = {
        entry["id"]: entry
        for entry in catalog.get("models", [])
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    updated: list[ModelTarget] = []
    for model in models:
        entry = entries.get(model.id) or entries.get(model.api_model or "")
        if entry is None or model.extra.get("price_override") is True:
            updated.append(
                replace(
                    model,
                    pricing_source=(
                        "manual_override"
                        if model.extra.get("price_override") is True
                        else model.pricing_source
                    ),
                )
            )
            continue

        updated.append(
            replace(
                model,
                input_price_per_1m=float(entry["input_price_per_1m"]),
                output_price_per_1m=float(entry["output_price_per_1m"]),
                pricing_source=entry["source"],
                pricing_source_url=entry.get("source_url"),
                pricing_updated_at=entry.get("last_updated"),
            )
        )
    return updated


def _require_non_negative_number(
    data: dict[str, Any],
    field: str,
    index: int,
) -> None:
    value = data.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(
            f"Pricing catalog model {index} field '{field}' must be a non-negative number."
        )
