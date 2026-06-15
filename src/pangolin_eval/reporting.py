from __future__ import annotations

import json
from dataclasses import asdict
from html import escape
from pathlib import Path

from pangolin_eval.models import ModelSummary, RagReport, RunReport, TraceCardReport


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


def write_rag_report(report: RagReport, out_dir: str | Path) -> tuple[Path, Path]:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "rag_report.json"
    markdown_path = output_path / "rag_report.md"

    json_path.write_text(
        json.dumps(asdict(report), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_rag_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def write_tracecard_report(
    report: TraceCardReport,
    out_dir: str | Path,
) -> tuple[Path, Path]:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "tracecards.json"
    markdown_path = output_path / "tracecards.md"

    json_path.write_text(
        json.dumps(asdict(report), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_tracecard_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def write_html_report(report: RunReport, out_dir: str | Path) -> Path:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    html_path = output_path / "report.html"
    html_path.write_text(render_html_report(report), encoding="utf-8")
    return html_path


def write_rag_html_report(report: RagReport, out_dir: str | Path) -> Path:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    html_path = output_path / "rag_report.html"
    html_path.write_text(render_rag_html_report(report), encoding="utf-8")
    return html_path


def write_tracecard_html_report(
    report: TraceCardReport,
    out_dir: str | Path,
) -> Path:
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    html_path = output_path / "tracecards.html"
    html_path.write_text(render_tracecard_html_report(report), encoding="utf-8")
    return html_path


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
                markdown_table_row(
                    [
                        gate_result.name,
                        result,
                        f"{gate_result.actual:.6f}",
                        f"{gate_result.threshold:.6f}",
                        gate_result.comparator,
                    ]
                )
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
                markdown_table_row(
                    [
                        aggregation.group_by,
                        aggregation.key,
                        aggregation.runs,
                        f"{aggregation.success_rate:.2f}",
                        format_optional_float(aggregation.avg_quality),
                        f"{aggregation.avg_latency_ms:.0f}",
                        f"{aggregation.total_cost_usd:.8f}",
                    ]
                )
            )

    if report.recommendations:
        lines.extend(
            [
                "",
                "## Recommendations",
                "",
                "| Category | Recommendation | Risk | Confidence | Evidence | Savings USD |",
                "| --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for recommendation in report.recommendations:
            savings = (
                f"{recommendation.expected_savings_usd:.8f}"
                if recommendation.expected_savings_usd is not None
                else "n/a"
            )
            lines.append(
                markdown_table_row(
                    [
                        recommendation.category,
                        recommendation.title,
                        recommendation.quality_risk,
                        recommendation.confidence,
                        recommendation.evidence,
                        savings,
                    ]
                )
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
            lines.extend(render_text_fence(result.response))
    return "\n".join(lines)


def render_rag_markdown(report: RagReport) -> str:
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
            "## RAG Results",
            "",
            "| Model | Question | Coverage | Faithfulness | Context tokens | Answer tokens | Context efficiency | Unused context | Repeated context | Oversized context | Missing citation | Cost USD | Cost per covered answer |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for result in report.results:
        lines.append(
            markdown_table_row(
                [
                    result.model_id,
                    result.question_id,
                    format_optional_float(result.answer_coverage),
                    format_optional_float(result.faithfulness_score),
                    result.retrieved_context_tokens,
                    result.answer_tokens,
                    format_optional_float(result.context_efficiency),
                    f"{result.unused_context_signal:.2f}",
                    f"{result.repeated_context_signal:.2f}",
                    "yes" if result.oversized_context else "no",
                    "yes" if result.missing_citation else "no",
                    f"{result.estimated_cost_usd:.8f}",
                    format_optional_cost(result.cost_per_covered_answer_usd),
                ]
            )
        )

    lines.extend(["", "## Answers", ""])
    for result in report.results:
        lines.extend(
            [
                f"### {result.model_id} / {result.question_id}",
                "",
                f"- Status: {result.status}",
                f"- Latency: {result.latency_ms} ms",
                f"- Retrieved context tokens: {result.retrieved_context_tokens}",
                f"- Answer tokens: {result.answer_tokens}",
                f"- Repeated context signal: {result.repeated_context_signal:.2f}",
                f"- Oversized context: {'yes' if result.oversized_context else 'no'}",
                "",
            ]
        )
        if result.error:
            lines.extend([f"- Error: {result.error}", ""])
        if result.response is None:
            lines.extend(
                [
                    "_Response content omitted or unavailable._",
                    "",
                ]
            )
        else:
            lines.extend(render_text_fence(result.response))
    return "\n".join(lines)


def render_tracecard_markdown(report: TraceCardReport) -> str:
    lines = [
        f"# {report.run_name}",
        "",
        f"- Schema version: `{report.schema_version}`",
        "",
    ]
    if report.description:
        lines.extend([report.description, ""])

    lines.extend(
        [
            "## TraceCards",
            "",
            "| Task | Outcome | Cost USD | Latency ms | Input tokens | Output tokens | Retries | Failures | Failed tools | Cache hits | Repeated steps | Wasted cost USD | Loop risk | Cost per success |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for card in report.tracecards:
        cost_per_success = (
            f"{card.cost_per_successful_task_usd:.8f}"
            if card.cost_per_successful_task_usd is not None
            else "n/a"
        )
        lines.append(
            markdown_table_row(
                [
                    card.task_id,
                    card.outcome,
                    f"{card.total_cost_usd:.8f}",
                    card.total_latency_ms,
                    card.input_tokens,
                    card.output_tokens,
                    card.retry_count,
                    card.failure_count,
                    card.failed_tool_call_count,
                    card.cache_hit_count,
                    card.repeated_step_count,
                    f"{card.wasted_cost_usd:.8f}",
                    "yes" if card.loop_risk else "no",
                    cost_per_success,
                ]
            )
        )

    lines.extend(["", "## Events", ""])
    for card in report.tracecards:
        lines.extend([f"### {card.task_id}", ""])
        for event in card.events:
            status = "success" if event.success else "failed"
            lines.append(
                f"- `{event.event_type}` `{event.name}`: {status}, "
                f"${event.estimated_cost_usd:.8f}, {event.latency_ms} ms"
            )
            if event.error:
                lines.append(f"  Error: {event.error}")
        lines.append("")
    return "\n".join(lines)


def render_html_report(report: RunReport) -> str:
    rows = [
        [
            summary.model_id,
            str(summary.runs),
            f"{summary.success_rate:.2f}",
            format_optional_float(summary.avg_quality),
            f"{summary.avg_latency_ms:.0f}",
            f"{summary.total_cost_usd:.8f}",
            format_optional_float(summary.efficiency_score),
            summary.recommendation,
        ]
        for summary in report.summaries
    ]
    sections = [
        html_table(
            "Model Summary",
            [
                "Model",
                "Runs",
                "Success rate",
                "Avg quality",
                "Avg latency ms",
                "Cost USD",
                "Efficiency",
                "Recommendation",
            ],
            rows,
        )
    ]
    if report.gate_results:
        sections.append(
            html_table(
                "Gate Results",
                ["Gate", "Result", "Actual", "Threshold", "Rule"],
                [
                    [
                        gate.name,
                        "pass" if gate.passed else "fail",
                        f"{gate.actual:.6f}",
                        f"{gate.threshold:.6f}",
                        gate.comparator,
                    ]
                    for gate in report.gate_results
                ],
            )
        )
    sections.append(
        html_table(
            "Prompt Results",
            ["Model", "Prompt", "Status", "Quality", "Latency ms", "Cost USD"],
            [
                [
                    result.model_id,
                    result.prompt_id,
                    result.status,
                    format_optional_float(result.quality_score),
                    str(result.latency_ms),
                    f"{result.estimated_cost_usd:.8f}",
                ]
                for result in report.results
            ],
        )
    )
    return html_page(report.run_name, report.description, sections)


def render_rag_html_report(report: RagReport) -> str:
    sections = [
        html_table(
            "RAG Results",
            [
                "Model",
                "Question",
                "Coverage",
                "Faithfulness",
                "Context tokens",
                "Context efficiency",
                "Unused context",
                "Repeated context",
                "Oversized context",
                "Missing citation",
                "Cost USD",
                "Cost per covered answer",
            ],
            [
                [
                    result.model_id,
                    result.question_id,
                    format_optional_float(result.answer_coverage),
                    format_optional_float(result.faithfulness_score),
                    str(result.retrieved_context_tokens),
                    format_optional_float(result.context_efficiency),
                    f"{result.unused_context_signal:.2f}",
                    f"{result.repeated_context_signal:.2f}",
                    "yes" if result.oversized_context else "no",
                    "yes" if result.missing_citation else "no",
                    f"{result.estimated_cost_usd:.8f}",
                    format_optional_cost(result.cost_per_covered_answer_usd),
                ]
                for result in report.results
            ],
        )
    ]
    return html_page(report.run_name, report.description, sections)


def render_tracecard_html_report(report: TraceCardReport) -> str:
    sections = [
        html_table(
            "TraceCards",
            [
                "Task",
                "Outcome",
                "Cost USD",
                "Latency ms",
                "Retries",
                "Failures",
                "Failed tools",
                "Wasted cost USD",
                "Loop risk",
            ],
            [
                [
                    card.task_id,
                    card.outcome,
                    f"{card.total_cost_usd:.8f}",
                    str(card.total_latency_ms),
                    str(card.retry_count),
                    str(card.failure_count),
                    str(card.failed_tool_call_count),
                    f"{card.wasted_cost_usd:.8f}",
                    "yes" if card.loop_risk else "no",
                ]
                for card in report.tracecards
            ],
        )
    ]
    return html_page(report.run_name, report.description, sections)


def html_page(title: str, description: str, sections: list[str]) -> str:
    description_html = f"<p>{escape(description)}</p>" if description else ""
    body = "\n".join(sections)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{escape(title)}</title>",
            "<style>",
            "body{font-family:system-ui,-apple-system,sans-serif;margin:2rem;line-height:1.5;color:#172033}",
            "table{border-collapse:collapse;width:100%;margin:1rem 0 2rem}",
            "th,td{border:1px solid #d7dde8;padding:.5rem;text-align:left}",
            "th{background:#f4f7fb}",
            "code,pre{background:#f4f7fb;padding:.15rem .3rem}",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{escape(title)}</h1>",
            description_html,
            body,
            "</body>",
            "</html>",
        ]
    )


def html_table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    header_cells = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(cell)}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    if not body_rows:
        body_rows.append(
            f'<tr><td colspan="{len(headers)}">No rows.</td></tr>'
        )
    return "\n".join(
        [
            f"<h2>{escape(title)}</h2>",
            "<table>",
            f"<thead><tr>{header_cells}</tr></thead>",
            "<tbody>",
            *body_rows,
            "</tbody>",
            "</table>",
        ]
    )


def render_summary_row(summary: ModelSummary) -> str:
    avg_quality = format_optional_float(summary.avg_quality)
    efficiency = format_optional_float(summary.efficiency_score)
    return markdown_table_row(
        [
            summary.model_id,
            summary.runs,
            f"{summary.success_rate:.2f}",
            avg_quality,
            f"{summary.avg_latency_ms:.0f}",
            f"{summary.max_latency_ms:.0f}",
            f"{summary.total_cost_usd:.8f}",
            efficiency,
            summary.recommendation,
        ]
    )


def markdown_table_row(cells: list[object]) -> str:
    return "| " + " | ".join(markdown_table_cell(cell) for cell in cells) + " |"


def markdown_table_cell(value: object) -> str:
    text = str(value)
    text = " ".join(text.splitlines())
    return text.replace("|", "\\|")


def format_optional_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def format_optional_cost(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.8f}"


def render_text_fence(text: str) -> list[str]:
    fence = "`" * max(3, longest_backtick_run(text) + 1)
    return [f"{fence}text", text, fence, ""]


def longest_backtick_run(text: str) -> int:
    longest = 0
    current = 0
    for char in text:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest
