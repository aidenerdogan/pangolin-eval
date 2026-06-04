from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


Message = dict[str, str]


@dataclass(frozen=True)
class PromptCase:
    id: str
    messages: list[Message]
    expected_keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModelTarget:
    id: str
    provider: str
    input_price_per_1m: float
    output_price_per_1m: float
    api_model: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    mock_latency_ms: int | None = None
    mock_response: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptResult:
    prompt_id: str
    model_id: str
    response: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    estimated_cost_usd: float
    quality_score: float | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelSummary:
    model_id: str
    runs: int
    avg_quality: float | None
    avg_latency_ms: float
    total_cost_usd: float
    efficiency_score: float | None
    recommendation: str


@dataclass(frozen=True)
class RunReport:
    run_name: str
    description: str
    results: list[PromptResult]
    summaries: list[ModelSummary]
