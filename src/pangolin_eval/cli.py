from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from pangolin_eval.config import load_config, parse_gates, parse_models, parse_prompts
from pangolin_eval.exports import load_json_artifact, write_otel_export
from pangolin_eval.gates import evaluate_gates, gates_passed
from pangolin_eval.pricing import apply_pricing_catalog, load_pricing_catalog
from pangolin_eval.rag import (
    load_rag_config,
    parse_documents,
    parse_questions,
    parse_rag_models,
    run_rag_evaluation,
)
from pangolin_eval.reporting import (
    write_html_report,
    write_rag_html_report,
    write_rag_report,
    write_reports,
    write_tracecard_html_report,
    write_tracecard_report,
)
from pangolin_eval.runner import run_comparison
from pangolin_eval.tracecards import generate_tracecard_report, load_trace_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pangolin-eval",
        description="Compare LLM workloads by cost, latency, and quality.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a model comparison.")
    run_parser.add_argument(
        "--config",
        required=True,
        help="Path to a JSON comparison config.",
    )
    run_parser.add_argument(
        "--out",
        required=True,
        help="Output directory for report.json and report.md.",
    )
    run_parser.add_argument(
        "--content-mode",
        choices=["full", "metadata-only"],
        default="full",
        help=(
            "Use 'metadata-only' to omit response text from saved reports while "
            "keeping metrics and scores."
        ),
    )
    run_parser.add_argument(
        "--html",
        action="store_true",
        help="Also write a static report.html artifact.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a comparison config without running providers.",
    )
    validate_parser.add_argument(
        "--config",
        required=True,
        help="Path to a JSON comparison config.",
    )

    rag_parser = subparsers.add_parser("rag", help="Run a RAG evaluation.")
    rag_parser.add_argument(
        "--config",
        required=True,
        help="Path to a JSON RAG evaluation config.",
    )
    rag_parser.add_argument(
        "--out",
        required=True,
        help="Output directory for rag_report.json and rag_report.md.",
    )
    rag_parser.add_argument(
        "--content-mode",
        choices=["full", "metadata-only"],
        default="full",
        help="Use 'metadata-only' to omit response text from saved RAG reports.",
    )
    rag_parser.add_argument(
        "--html",
        action="store_true",
        help="Also write a static rag_report.html artifact.",
    )

    trace_parser = subparsers.add_parser(
        "trace",
        help="Generate agent/workflow TraceCards from local trace events.",
    )
    trace_parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON trace-events file.",
    )
    trace_parser.add_argument(
        "--out",
        required=True,
        help="Output directory for tracecards.json and tracecards.md.",
    )
    trace_parser.add_argument(
        "--html",
        action="store_true",
        help="Also write a static tracecards.html artifact.",
    )

    export_parser = subparsers.add_parser(
        "export-otel",
        help="Export a PangolinEval artifact as OTel-style spans.",
    )
    export_parser.add_argument(
        "--input",
        required=True,
        help="Path to report.json or tracecards.json.",
    )
    export_parser.add_argument(
        "--out",
        required=True,
        help="Output JSON path for exported spans.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            return run_command(
                Path(args.config),
                Path(args.out),
                args.content_mode,
                args.html,
            )
        if args.command == "validate":
            return validate_command(Path(args.config))
        if args.command == "rag":
            return rag_command(
                Path(args.config),
                Path(args.out),
                args.content_mode,
                args.html,
            )
        if args.command == "trace":
            return trace_command(Path(args.input), Path(args.out), args.html)
        if args.command == "export-otel":
            return export_otel_command(Path(args.input), Path(args.out))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 1


def run_command(
    config_path: Path,
    out_dir: Path,
    content_mode: str = "full",
    include_html: bool = False,
) -> int:
    config = load_config(config_path)
    normalized_content_mode = content_mode.replace("-", "_")
    models = parse_models(config)
    if "pricing_catalog" in config:
        catalog_path = config_path.parent / config["pricing_catalog"]
        models = apply_pricing_catalog(models, load_pricing_catalog(catalog_path))
    report = run_comparison(
        run_name=config.get("run_name", config_path.stem),
        description=config.get("description", ""),
        models=models,
        prompts=parse_prompts(config),
        content_mode=normalized_content_mode,
    )
    gate_results = evaluate_gates(report, parse_gates(config))
    if gate_results:
        report = replace(report, gate_results=gate_results)
    json_path, markdown_path = write_reports(report, out_dir)
    print(f"Wrote JSON report: {json_path}")
    print(f"Wrote Markdown report: {markdown_path}")
    if include_html:
        html_path = write_html_report(report, out_dir)
        print(f"Wrote HTML report: {html_path}")
    if gate_results and not gates_passed(gate_results):
        print("One or more gates failed.", file=sys.stderr)
        return 3
    return 0


def validate_command(config_path: Path) -> int:
    load_config(config_path)
    print(f"Config is valid: {config_path}")
    return 0


def rag_command(
    config_path: Path,
    out_dir: Path,
    content_mode: str = "full",
    include_html: bool = False,
) -> int:
    config = load_rag_config(config_path)
    normalized_content_mode = content_mode.replace("-", "_")
    report = run_rag_evaluation(
        run_name=config.get("run_name", config_path.stem),
        description=config.get("description", ""),
        models=parse_rag_models(config),
        documents=parse_documents(config),
        questions=parse_questions(config),
        content_mode=normalized_content_mode,
        max_context_tokens=config.get("max_context_tokens"),
    )
    json_path, markdown_path = write_rag_report(report, out_dir)
    print(f"Wrote RAG JSON report: {json_path}")
    print(f"Wrote RAG Markdown report: {markdown_path}")
    if include_html:
        html_path = write_rag_html_report(report, out_dir)
        print(f"Wrote RAG HTML report: {html_path}")
    return 0


def trace_command(input_path: Path, out_dir: Path, include_html: bool = False) -> int:
    config = load_trace_config(input_path)
    report = generate_tracecard_report(config)
    json_path, markdown_path = write_tracecard_report(report, out_dir)
    print(f"Wrote TraceCard JSON report: {json_path}")
    print(f"Wrote TraceCard Markdown report: {markdown_path}")
    if include_html:
        html_path = write_tracecard_html_report(report, out_dir)
        print(f"Wrote TraceCard HTML report: {html_path}")
    return 0


def export_otel_command(input_path: Path, out_path: Path) -> int:
    output_path = write_otel_export(load_json_artifact(input_path), out_path)
    print(f"Wrote OTel-style export: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
