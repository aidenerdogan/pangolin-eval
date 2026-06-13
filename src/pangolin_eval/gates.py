from __future__ import annotations

from pangolin_eval.models import GateResult, RunReport


def evaluate_gates(report: RunReport, gates: dict[str, float]) -> list[GateResult]:
    results: list[GateResult] = []
    if not gates:
        return results

    successful_results = [result for result in report.results if result.success]
    total_cost = sum(result.estimated_cost_usd for result in report.results)
    max_prompt_cost = max(
        (result.estimated_cost_usd for result in report.results),
        default=0,
    )
    avg_latency = (
        sum(result.latency_ms for result in successful_results) / len(successful_results)
        if successful_results
        else 0
    )
    max_latency = max(
        (result.latency_ms for result in successful_results),
        default=0,
    )
    quality_values = [
        result.quality_score
        for result in successful_results
        if result.quality_score is not None
    ]
    avg_quality = (
        sum(quality_values) / len(quality_values)
        if quality_values
        else 0
    )
    success_rate = (
        len(successful_results) / len(report.results)
        if report.results
        else 0
    )

    checks = {
        "max_total_cost_usd": (total_cost, "<="),
        "max_prompt_cost_usd": (max_prompt_cost, "<="),
        "max_avg_latency_ms": (avg_latency, "<="),
        "max_latency_ms": (max_latency, "<="),
        "min_avg_quality": (avg_quality, ">="),
        "min_success_rate": (success_rate, ">="),
    }

    for name, threshold in gates.items():
        actual, comparator = checks[name]
        passed = actual <= threshold if comparator == "<=" else actual >= threshold
        results.append(
            GateResult(
                name=name,
                passed=passed,
                actual=actual,
                threshold=threshold,
                comparator=comparator,
                message=_gate_message(name, passed, actual, comparator, threshold),
            )
        )

    return results


def gates_passed(gate_results: list[GateResult]) -> bool:
    return all(result.passed for result in gate_results)


def _gate_message(
    name: str,
    passed: bool,
    actual: float,
    comparator: str,
    threshold: float,
) -> str:
    status = "passed" if passed else "failed"
    return f"{name} {status}: actual {actual:.6f} {comparator} threshold {threshold:.6f}"
