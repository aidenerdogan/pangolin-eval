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
    ]
    if report.description:
        lines.extend([report.description, ""])

    lines.extend(
        [
            "## Model Summary",
            "",
            "| Model | Runs | Avg quality | Avg latency ms | Estimated cost USD | Efficiency | Recommendation |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for summary in report.summaries:
        lines.append(render_summary_row(summary))

    lines.extend(["", "## Prompt Results", ""])
    for result in report.results:
        quality = format_optional_float(result.quality_score)
        lines.extend(
            [
                f"### {result.model_id} / {result.prompt_id}",
                "",
                f"- Quality score: {quality}",
                f"- Latency: {result.latency_ms} ms",
                f"- Input tokens: {result.input_tokens}",
                f"- Output tokens: {result.output_tokens}",
                f"- Estimated cost: ${result.estimated_cost_usd:.8f}",
                "",
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
        f"| {avg_quality} "
        f"| {summary.avg_latency_ms:.0f} "
        f"| {summary.total_cost_usd:.8f} "
        f"| {efficiency} "
        f"| {summary.recommendation} |"
    )


def format_optional_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"
