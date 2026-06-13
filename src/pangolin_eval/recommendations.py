from __future__ import annotations

from collections import Counter

from pangolin_eval.models import Recommendation, RunReport


def generate_recommendations(report: RunReport) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    recommendations.extend(model_switch_recommendations(report))
    recommendations.extend(reliability_recommendations(report))
    recommendations.extend(token_recommendations(report))
    recommendations.extend(caching_recommendations(report))
    return recommendations


def model_switch_recommendations(report: RunReport) -> list[Recommendation]:
    quality_summaries = [
        summary
        for summary in report.summaries
        if summary.avg_quality is not None and summary.success_rate == 1
    ]
    if len(quality_summaries) < 2:
        return []

    best_quality = max(quality_summaries, key=lambda summary: summary.avg_quality or 0)
    candidates = [
        summary
        for summary in quality_summaries
        if summary.model_id != best_quality.model_id
        and (best_quality.avg_quality or 0) - (summary.avg_quality or 0) <= 0.05
        and summary.total_cost_usd < best_quality.total_cost_usd
    ]
    if not candidates:
        return []

    cheapest = min(candidates, key=lambda summary: summary.total_cost_usd)
    savings = best_quality.total_cost_usd - cheapest.total_cost_usd
    return [
        Recommendation(
            id="model-switch-cheaper-candidate",
            category="model_switch",
            title=f"Review {cheapest.model_id} as a cheaper candidate",
            evidence=(
                f"{cheapest.model_id} is within 0.05 quality of "
                f"{best_quality.model_id} and costs ${savings:.8f} less in this run."
            ),
            expected_savings_usd=savings,
            quality_risk="low",
            confidence="medium",
            affected_models=[best_quality.model_id, cheapest.model_id],
        )
    ]


def reliability_recommendations(report: RunReport) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for summary in report.summaries:
        if summary.success_rate < 1:
            recommendations.append(
                Recommendation(
                    id=f"reliability-review-{summary.model_id}",
                    category="fallback_review",
                    title=f"Review fallback behavior for {summary.model_id}",
                    evidence=(
                        f"{summary.failure_count} of {summary.runs} runs failed "
                        f"for {summary.model_id}."
                    ),
                    expected_savings_usd=None,
                    quality_risk="medium",
                    confidence="high",
                    affected_models=[summary.model_id],
                )
            )
    return recommendations


def token_recommendations(report: RunReport) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for result in report.results:
        if result.input_tokens >= 1000:
            recommendations.append(
                Recommendation(
                    id=f"context-trim-{result.model_id}-{result.prompt_id}",
                    category="context_trimming",
                    title=f"Review context size for {result.prompt_id}",
                    evidence=(
                        f"{result.prompt_id} used {result.input_tokens} input tokens "
                        f"with {result.model_id}."
                    ),
                    expected_savings_usd=None,
                    quality_risk="medium",
                    confidence="medium",
                    affected_models=[result.model_id],
                    affected_prompts=[result.prompt_id],
                )
            )
        if result.output_tokens >= 500 and (result.quality_score or 0) >= 0.75:
            recommendations.append(
                Recommendation(
                    id=f"max-token-cap-{result.model_id}-{result.prompt_id}",
                    category="max_token_cap",
                    title=f"Consider a max-token cap for {result.prompt_id}",
                    evidence=(
                        f"{result.prompt_id} produced {result.output_tokens} output "
                        f"tokens while meeting the quality bar."
                    ),
                    expected_savings_usd=None,
                    quality_risk="low",
                    confidence="medium",
                    affected_models=[result.model_id],
                    affected_prompts=[result.prompt_id],
                )
            )
    return recommendations


def caching_recommendations(report: RunReport) -> list[Recommendation]:
    prompt_counts = Counter(result.prompt_id for result in report.results)
    repeated_prompts = [
        prompt_id for prompt_id, count in prompt_counts.items() if count > 1
    ]
    if not repeated_prompts:
        return []
    return [
        Recommendation(
            id="cache-repeated-prompts",
            category="caching",
            title="Review caching for repeated prompts",
            evidence=(
                "The run evaluated repeated prompt ids across model candidates: "
                + ", ".join(sorted(repeated_prompts))
            ),
            expected_savings_usd=None,
            quality_risk="low",
            confidence="low",
            affected_prompts=sorted(repeated_prompts),
        )
    ]
