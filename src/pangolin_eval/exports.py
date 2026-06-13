from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OTEL_EXPORT_SCHEMA_VERSION = "pangolin-eval.otel_export.v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    with artifact_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input artifact must be a JSON object.")
    return data


def export_otel_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    schema_version = artifact.get("schema_version", "")
    if isinstance(schema_version, str) and schema_version.startswith("pangolin-eval.report."):
        spans = report_spans(artifact)
    elif schema_version == "pangolin-eval.tracecards.v1":
        spans = tracecard_spans(artifact)
    else:
        raise ValueError(f"Unsupported artifact schema_version '{schema_version}'.")
    return {
        "schema_version": OTEL_EXPORT_SCHEMA_VERSION,
        "spans": spans,
    }


def write_otel_export(artifact: dict[str, Any], out_path: str | Path) -> Path:
    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = export_otel_artifact(artifact)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def report_spans(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for result in artifact.get("results", []):
        if not isinstance(result, dict):
            continue
        spans.append(
            {
                "name": f"{result.get('model_id')}/{result.get('prompt_id')}",
                "kind": "llm",
                "status": result.get("status", "success"),
                "attributes": {
                    "pangolin.prompt_id": result.get("prompt_id"),
                    "pangolin.model_id": result.get("model_id"),
                    "pangolin.feature": result.get("feature"),
                    "pangolin.workflow": result.get("workflow"),
                    "llm.usage.input_tokens": result.get("input_tokens", 0),
                    "llm.usage.output_tokens": result.get("output_tokens", 0),
                    "pangolin.estimated_cost_usd": result.get("estimated_cost_usd", 0),
                    "pangolin.quality_score": result.get("quality_score"),
                    "pangolin.success": result.get("success", True),
                },
            }
        )
    return spans


def tracecard_spans(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for card in artifact.get("tracecards", []):
        if not isinstance(card, dict):
            continue
        for event in card.get("events", []):
            if not isinstance(event, dict):
                continue
            spans.append(
                {
                    "name": event.get("name"),
                    "kind": event.get("event_type"),
                    "status": "success" if event.get("success", True) else "error",
                    "attributes": {
                        "pangolin.task_id": card.get("task_id"),
                        "pangolin.event_id": event.get("id"),
                        "pangolin.model_id": event.get("model_id"),
                        "llm.usage.input_tokens": event.get("input_tokens", 0),
                        "llm.usage.output_tokens": event.get("output_tokens", 0),
                        "pangolin.estimated_cost_usd": event.get("estimated_cost_usd", 0),
                        "pangolin.latency_ms": event.get("latency_ms", 0),
                        "pangolin.retry_count": event.get("retry_count", 0),
                        "pangolin.cache_hit": event.get("cache_hit", False),
                    },
                }
            )
    return spans
