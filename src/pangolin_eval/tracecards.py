from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pangolin_eval.models import TraceCard, TraceCardReport, TraceEvent

TRACE_EVENTS_SCHEMA_VERSION = "pangolin-eval.trace_events.v1"


def load_trace_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate_trace_config(data)
    return data


def validate_trace_config(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("Trace config must be a JSON object.")
    if data.get("schema_version") != TRACE_EVENTS_SCHEMA_VERSION:
        raise ValueError(
            f"Trace config schema_version must be '{TRACE_EVENTS_SCHEMA_VERSION}'."
        )
    traces = data.get("traces")
    if not isinstance(traces, list) or not traces:
        raise ValueError("Trace config must include a non-empty 'traces' list.")
    for index, trace in enumerate(traces, start=1):
        if not isinstance(trace, dict):
            raise ValueError(f"Trace {index} must be an object.")
        _require_string(trace, "task_id", f"Trace {index}")
        _require_string(trace, "outcome", f"Trace {index}")
        events = trace.get("events")
        if not isinstance(events, list) or not events:
            raise ValueError(f"Trace {index} must include non-empty events.")
        event_ids: set[str] = set()
        for event_index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                raise ValueError(f"Trace {index} event {event_index} must be an object.")
            event_id = _require_string(event, "id", f"Trace {index} event {event_index}")
            _require_string(event, "event_type", f"Trace {index} event {event_index}")
            _require_string(event, "name", f"Trace {index} event {event_index}")
            if event_id in event_ids:
                raise ValueError(f"Trace {index} event id '{event_id}' must be unique.")
            event_ids.add(event_id)
            for field in [
                "input_tokens",
                "output_tokens",
                "latency_ms",
                "retry_count",
            ]:
                if field in event:
                    _require_non_negative_integer(
                        event,
                        field,
                        f"Trace {index} event {event_index}",
                    )
            if "estimated_cost_usd" in event:
                _require_non_negative_number(
                    event,
                    "estimated_cost_usd",
                    f"Trace {index} event {event_index}",
                )
            for field in ["success", "cache_hit"]:
                if field in event and not isinstance(event[field], bool):
                    raise ValueError(
                        f"Trace {index} event {event_index} field '{field}' must be a boolean."
                    )


def generate_tracecard_report(data: dict[str, Any]) -> TraceCardReport:
    tracecards = [
        generate_tracecard(trace["task_id"], trace["outcome"], trace["events"])
        for trace in data["traces"]
    ]
    return TraceCardReport(
        run_name=data.get("run_name", "tracecards"),
        description=data.get("description", ""),
        tracecards=tracecards,
    )


def generate_tracecard(
    task_id: str,
    outcome: str,
    raw_events: list[dict[str, Any]],
) -> TraceCard:
    events = [parse_event(event) for event in raw_events]
    success = outcome == "success" and all(event.success for event in events)
    total_cost = sum(event.estimated_cost_usd for event in events)
    total_latency = sum(event.latency_ms for event in events)
    repeated_step_count = repeated_steps(events)
    retry_count = sum(event.retry_count for event in events)
    failure_count = sum(1 for event in events if not event.success)
    failed_tool_call_count = sum(
        1
        for event in events
        if event.event_type == "tool_call" and not event.success
    )
    wasted_cost = sum(
        event.estimated_cost_usd
        for event in events
        if not event.success or event.retry_count > 0 or event.event_type == "retry"
    )
    return TraceCard(
        task_id=task_id,
        outcome=outcome,
        success=success,
        events=events,
        total_cost_usd=total_cost,
        total_latency_ms=total_latency,
        input_tokens=sum(event.input_tokens for event in events),
        output_tokens=sum(event.output_tokens for event in events),
        retry_count=retry_count,
        failure_count=failure_count,
        cache_hit_count=sum(1 for event in events if event.cache_hit),
        repeated_step_count=repeated_step_count,
        cost_per_successful_task_usd=total_cost if success else None,
        failed_tool_call_count=failed_tool_call_count,
        wasted_cost_usd=wasted_cost,
        loop_risk=repeated_step_count > 0 or retry_count > 0,
    )


def parse_event(event: dict[str, Any]) -> TraceEvent:
    return TraceEvent(
        id=event["id"],
        event_type=event["event_type"],
        name=event["name"],
        input_tokens=int(event.get("input_tokens", 0)),
        output_tokens=int(event.get("output_tokens", 0)),
        latency_ms=int(event.get("latency_ms", 0)),
        estimated_cost_usd=float(event.get("estimated_cost_usd", 0)),
        success=bool(event.get("success", True)),
        error=event.get("error"),
        retry_count=int(event.get("retry_count", 0)),
        cache_hit=bool(event.get("cache_hit", False)),
        model_id=event.get("model_id"),
        parent_id=event.get("parent_id"),
    )


def repeated_steps(events: list[TraceEvent]) -> int:
    counts = Counter((event.event_type, event.name) for event in events)
    return sum(count - 1 for count in counts.values() if count > 1)


def _require_string(data: dict[str, Any], field: str, owner: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} field '{field}' must be a non-empty string.")
    return value


def _require_non_negative_integer(
    data: dict[str, Any],
    field: str,
    owner: str,
) -> int:
    value = data.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{owner} field '{field}' must be a non-negative integer.")
    return value


def _require_non_negative_number(
    data: dict[str, Any],
    field: str,
    owner: str,
) -> float:
    value = data.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{owner} field '{field}' must be a non-negative number.")
    return float(value)
