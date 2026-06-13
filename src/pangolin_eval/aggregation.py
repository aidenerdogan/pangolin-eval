from __future__ import annotations

from collections import defaultdict

from pangolin_eval.models import AggregationSummary, PromptResult

AGGREGATION_FIELDS = [
    "model_id",
    "prompt_id",
    "model_group",
    "feature",
    "workflow",
    "environment",
    "prompt_version",
]


def summarize_aggregations(results: list[PromptResult]) -> list[AggregationSummary]:
    aggregations: list[AggregationSummary] = []
    for field in AGGREGATION_FIELDS:
        grouped: dict[str, list[PromptResult]] = defaultdict(list)
        for result in results:
            value = getattr(result, field)
            key = str(value) if value else "unattributed"
            grouped[key].append(result)

        for key, grouped_results in grouped.items():
            aggregations.append(_summarize_group(field, key, grouped_results))

    return sorted(
        aggregations,
        key=lambda summary: (
            summary.group_by,
            -summary.total_cost_usd,
            summary.key,
        ),
    )


def _summarize_group(
    group_by: str,
    key: str,
    results: list[PromptResult],
) -> AggregationSummary:
    successful = [result for result in results if result.success]
    quality_values = [
        result.quality_score
        for result in successful
        if result.quality_score is not None
    ]
    avg_quality = (
        sum(quality_values) / len(quality_values)
        if quality_values
        else None
    )
    avg_latency = (
        sum(result.latency_ms for result in successful) / len(successful)
        if successful
        else 0
    )
    return AggregationSummary(
        group_by=group_by,
        key=key,
        runs=len(results),
        success_count=len(successful),
        failure_count=len(results) - len(successful),
        success_rate=len(successful) / len(results) if results else 0,
        avg_quality=avg_quality,
        avg_latency_ms=avg_latency,
        total_cost_usd=sum(result.estimated_cost_usd for result in results),
    )
