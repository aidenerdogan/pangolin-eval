from __future__ import annotations

from collections import defaultdict

from pangolin_eval.models import (
    SUPPORTED_CONTENT_MODES,
    ModelSummary,
    ModelTarget,
    PromptCase,
    PromptResult,
    RunReport,
)
from pangolin_eval.providers import MockProvider, OpenAICompatibleProvider, Provider
from pangolin_eval.scoring import estimate_cost_usd, keyword_quality_score


def run_comparison(
    run_name: str,
    description: str,
    models: list[ModelTarget],
    prompts: list[PromptCase],
    content_mode: str = "full",
) -> RunReport:
    if content_mode not in SUPPORTED_CONTENT_MODES:
        supported = ", ".join(sorted(SUPPORTED_CONTENT_MODES))
        raise ValueError(
            f"Unsupported content mode '{content_mode}'. Supported modes: {supported}."
        )

    results: list[PromptResult] = []

    for model in models:
        provider = provider_for(model)
        for prompt in prompts:
            completion = provider.complete(model, prompt)
            quality_score = keyword_quality_score(completion.text, prompt.expected_keywords)
            estimated_cost = estimate_cost_usd(
                completion.input_tokens,
                completion.output_tokens,
                model.input_price_per_1m,
                model.output_price_per_1m,
            )
            metadata = completion.metadata
            response = completion.text
            if content_mode == "metadata_only":
                metadata = {**completion.metadata, "response_content_omitted": True}
                response = None
            results.append(
                PromptResult(
                    prompt_id=prompt.id,
                    model_id=model.id,
                    response=response,
                    input_tokens=completion.input_tokens,
                    output_tokens=completion.output_tokens,
                    latency_ms=completion.latency_ms,
                    estimated_cost_usd=estimated_cost,
                    quality_score=quality_score,
                    metadata=metadata,
                )
            )

    summaries = summarize_results(results)
    return RunReport(
        run_name=run_name,
        description=description,
        results=results,
        summaries=summaries,
        content_mode=content_mode,
    )


def provider_for(model: ModelTarget) -> Provider:
    if model.provider == "mock":
        return MockProvider()
    if model.provider == "openai_compatible":
        return OpenAICompatibleProvider()
    raise ValueError(f"Unknown provider '{model.provider}' for model {model.id}.")


def summarize_results(results: list[PromptResult]) -> list[ModelSummary]:
    grouped: dict[str, list[PromptResult]] = defaultdict(list)
    for result in results:
        grouped[result.model_id].append(result)

    summaries: list[ModelSummary] = []
    for model_id, model_results in grouped.items():
        quality_values = [
            result.quality_score
            for result in model_results
            if result.quality_score is not None
        ]
        avg_quality = (
            sum(quality_values) / len(quality_values)
            if quality_values
            else None
        )
        avg_latency = sum(result.latency_ms for result in model_results) / len(model_results)
        total_cost = sum(result.estimated_cost_usd for result in model_results)
        efficiency = efficiency_score(avg_quality, avg_latency, total_cost)
        summaries.append(
            ModelSummary(
                model_id=model_id,
                runs=len(model_results),
                avg_quality=avg_quality,
                avg_latency_ms=avg_latency,
                total_cost_usd=total_cost,
                efficiency_score=efficiency,
                recommendation=recommendation(avg_quality, avg_latency, total_cost),
            )
        )

    return sorted(
        summaries,
        key=lambda summary: (
            summary.efficiency_score is None,
            -(summary.efficiency_score or 0),
            summary.total_cost_usd,
        ),
    )


def efficiency_score(
    avg_quality: float | None,
    avg_latency_ms: float,
    total_cost_usd: float,
) -> float | None:
    if avg_quality is None:
        return None
    latency_penalty = max(avg_latency_ms, 1) / 1000
    cost_penalty = max(total_cost_usd, 0.000001) * 1000
    return avg_quality / (1 + latency_penalty + cost_penalty)


def recommendation(
    avg_quality: float | None,
    avg_latency_ms: float,
    total_cost_usd: float,
) -> str:
    if avg_quality is None:
        return "Needs quality scoring"
    if avg_quality >= 0.95 and total_cost_usd < 0.001:
        return "Best quality candidate"
    if avg_quality >= 0.75 and avg_latency_ms <= 350:
        return "Good baseline"
    if avg_quality >= 0.75:
        return "Usable with latency review"
    return "Needs improvement"
