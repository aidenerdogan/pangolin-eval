from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from pangolin_eval.models import ModelSummary, RunReport


def write_reports(report: RunReport, out_dir: str | Path) -> tuple[Path, Path]:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "report.json"
    markdown_path = output_path / "report.md"

    json_path.write_text(
        json.dumps(asdict(report), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def render_markdown(report: RunReport) -> str:
    lines = [
        f"# {report.run_name}",
        "",
        f"- Schema version: `{report.schema_version}`",
        f"- Content mode: `{report.content_mode}`",
        "",
    ]
    if report.description:
        lines.extend([report.description, ""])

    lines.extend(
        [
            "## Model Summary",
            "",
            "| Model | Runs | Success rate | Avg quality | Avg latency ms | Max latency ms | Estimated cost USD | Efficiency | Recommendation |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for summary in report.summaries:
        lines.append(render_summary_row(summary))

    if report.gate_results:
        lines.extend(
            [
                "",
                "## Gate Results",
                "",
                "| Gate | Result | Actual | Threshold | Rule |",
                "| --- | --- | ---: | ---: | --- |",
            ]
        )
        for gate_result in report.gate_results:
            result = "pass" if gate_result.passed else "fail"
            lines.append(
                f"| {gate_result.name} "
                f"| {result} "
                f"| {gate_result.actual:.6f} "
                f"| {gate_result.threshold:.6f} "
                f"| {gate_result.comparator} |"
            )

    if report.aggregations:
        lines.extend(
            [
                "",
                "## Attribution Summary",
                "",
                "| Group by | Key | Runs | Success rate | Avg quality | Avg latency ms | Estimated cost USD |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for aggregation in report.aggregations[:25]:
            lines.append(
                f"| {aggregation.group_by} "
                f"| {aggregation.key} "
                f"| {aggregation.runs} "
                f"| {aggregation.success_rate:.2f} "
                f"| {format_optional_float(aggregation.avg_quality)} "
                f"| {aggregation.avg_latency_ms:.0f} "
                f"| {aggregation.total_cost_usd:.8f} |"
            )

    lines.extend(["", "## Prompt Results", ""])
    for result in report.results:
        quality = format_optional_float(result.quality_score)
        lines.extend(
            [
                f"### {result.model_id} / {result.prompt_id}",
                "",
                f"- Status: {result.status}",
                f"- Quality score: {quality}",
                f"- Latency: {result.latency_ms} ms",
                f"- Input tokens: {result.input_tokens}",
                f"- Output tokens: {result.output_tokens}",
                f"- Estimated cost: ${result.estimated_cost_usd:.8f}",
                f"- Retries: {result.retry_count}",
                "",
            ]
        )
        if result.error:
            lines.extend([f"- Error: {result.error}", ""])
        if result.response is None:
            lines.extend(
                [
                    "_Response content omitted because content mode is metadata_only._",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "```text",
                    result.response,
                    "```",
                    "",
                ]
            )
    return "\n".join(lines)


def render_summary_row(summary: ModelSummary) -> str:
    avg_quality = format_optional_float(summary.avg_quality)
    efficiency = format_optional_float(summary.efficiency_score)
    return (
        f"| {summary.model_id} "
        f"| {summary.runs} "
        f"| {summary.success_rate:.2f} "
        f"| {avg_quality} "
        f"| {summary.avg_latency_ms:.0f} "
        f"| {summary.max_latency_ms:.0f} "
        f"| {summary.total_cost_usd:.8f} "
        f"| {efficiency} "
        f"| {summary.recommendation} |"
    )


def format_optional_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"
