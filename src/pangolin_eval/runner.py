from __future__ import annotations

from collections import defaultdict

from pangolin_eval.aggregation import summarize_aggregations
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
            completion, retry_count, error, timed_out = complete_with_retries(
                provider,
                model,
                prompt,
            )
            if error is not None:
                results.append(
                    failed_result(
                        model=model,
                        prompt=prompt,
                        error=error,
                        retry_count=retry_count,
                        timed_out=timed_out,
                    )
                )
                continue

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
                    success=True,
                    status="success",
                    retry_count=retry_count,
                    usage_source=completion.usage_source,
                    model_group=model.model_group,
                    feature=prompt.feature,
                    workflow=prompt.workflow,
                    environment=prompt.environment,
                    prompt_version=prompt.prompt_version,
                    customer_user_hash=prompt.customer_user_hash,
                    pricing_source=model.pricing_source,
                    pricing_source_url=model.pricing_source_url,
                    pricing_updated_at=model.pricing_updated_at,
                    metadata=metadata,
                )
            )

    summaries = summarize_results(results)
    aggregations = summarize_aggregations(results)
    return RunReport(
        run_name=run_name,
        description=description,
        results=results,
        summaries=summaries,
        aggregations=aggregations,
        content_mode=content_mode,
    )


def complete_with_retries(
    provider: Provider,
    model: ModelTarget,
    prompt: PromptCase,
):
    attempts = model.max_retries + 1
    last_error: Exception | None = None
    timed_out = False

    for attempt in range(attempts):
        try:
            completion = provider.complete(model, prompt)
            return completion, attempt, None, False
        except Exception as exc:  # noqa: BLE001 - provider adapters normalize later.
            last_error = exc
            timed_out = timed_out or is_timeout_error(exc)

    assert last_error is not None
    return None, max(attempts - 1, 0), sanitize_error(last_error), timed_out


def failed_result(
    model: ModelTarget,
    prompt: PromptCase,
    error: str,
    retry_count: int,
    timed_out: bool,
) -> PromptResult:
    return PromptResult(
        prompt_id=prompt.id,
        model_id=model.id,
        response=None,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        estimated_cost_usd=0,
        quality_score=None,
        success=False,
        status="timeout" if timed_out else "error",
        error=error,
        retry_count=retry_count,
        timed_out=timed_out,
        model_group=model.model_group,
        feature=prompt.feature,
        workflow=prompt.workflow,
        environment=prompt.environment,
        prompt_version=prompt.prompt_version,
        customer_user_hash=prompt.customer_user_hash,
        pricing_source=model.pricing_source,
        pricing_source_url=model.pricing_source_url,
        pricing_updated_at=model.pricing_updated_at,
        metadata={"provider": model.provider},
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
        successful_results = [result for result in model_results if result.success]
        success_count = len(successful_results)
        failure_count = len(model_results) - success_count
        success_rate = success_count / len(model_results) if model_results else 0
        quality_values = [
            result.quality_score
            for result in successful_results
            if result.quality_score is not None
        ]
        avg_quality = (
            sum(quality_values) / len(quality_values)
            if quality_values
            else None
        )
        avg_latency = (
            sum(result.latency_ms for result in successful_results) / success_count
            if successful_results
            else 0
        )
        max_latency = max((result.latency_ms for result in successful_results), default=0)
        total_cost = sum(result.estimated_cost_usd for result in model_results)
        efficiency = efficiency_score(avg_quality, avg_latency, total_cost)
        summaries.append(
            ModelSummary(
                model_id=model_id,
                runs=len(model_results),
                success_count=success_count,
                failure_count=failure_count,
                success_rate=success_rate,
                avg_quality=avg_quality,
                avg_latency_ms=avg_latency,
                max_latency_ms=max_latency,
                total_cost_usd=total_cost,
                efficiency_score=efficiency,
                recommendation=recommendation(
                    avg_quality,
                    avg_latency,
                    total_cost,
                    success_rate,
                ),
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
    success_rate: float = 1.0,
) -> str:
    if success_rate == 0:
        return "Provider failures"
    if success_rate < 1:
        return "Review reliability"
    if avg_quality is None:
        return "Needs quality scoring"
    if avg_quality >= 0.95 and total_cost_usd < 0.001:
        return "Best quality candidate"
    if avg_quality >= 0.75 and avg_latency_ms <= 350:
        return "Good baseline"
    if avg_quality >= 0.75:
        return "Usable with latency review"
    return "Needs improvement"


def sanitize_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        message = exc.__class__.__name__
    text = f"{exc.__class__.__name__}: {message}"
    return text[:300]


def is_timeout_error(exc: Exception) -> bool:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    return "timeout" in name or "timed out" in message or "timeout" in message
