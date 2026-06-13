from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


Message = dict[str, str]
REPORT_SCHEMA_VERSION = "pangolin-eval.report.v3"
RAG_REPORT_SCHEMA_VERSION = "pangolin-eval.rag_report.v1"
SUPPORTED_CONTENT_MODES = {"full", "metadata_only"}


@dataclass(frozen=True)
class PromptCase:
    id: str
    messages: list[Message]
    expected_keywords: list[str] = field(default_factory=list)
    feature: str | None = None
    workflow: str | None = None
    environment: str | None = None
    prompt_version: str | None = None
    customer_user_hash: str | None = None


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
    max_retries: int = 0
    model_group: str | None = None
    pricing_source: str = "manual"
    pricing_source_url: str | None = None
    pricing_updated_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
    usage_source: str = "estimated"


@dataclass(frozen=True)
class PromptResult:
    prompt_id: str
    model_id: str
    response: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: int
    estimated_cost_usd: float
    quality_score: float | None
    success: bool = True
    status: str = "success"
    error: str | None = None
    retry_count: int = 0
    timed_out: bool = False
    usage_source: str = "estimated"
    model_group: str | None = None
    feature: str | None = None
    workflow: str | None = None
    environment: str | None = None
    prompt_version: str | None = None
    customer_user_hash: str | None = None
    pricing_source: str = "manual"
    pricing_source_url: str | None = None
    pricing_updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelSummary:
    model_id: str
    runs: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_quality: float | None
    avg_latency_ms: float
    max_latency_ms: int
    total_cost_usd: float
    efficiency_score: float | None
    recommendation: str


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    actual: float
    threshold: float
    comparator: str
    scope: str = "run"
    message: str = ""


@dataclass(frozen=True)
class AggregationSummary:
    group_by: str
    key: str
    runs: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_quality: float | None
    avg_latency_ms: float
    total_cost_usd: float


@dataclass(frozen=True)
class RunReport:
    run_name: str
    description: str
    results: list[PromptResult]
    summaries: list[ModelSummary]
    gate_results: list[GateResult] = field(default_factory=list)
    aggregations: list[AggregationSummary] = field(default_factory=list)
    schema_version: str = REPORT_SCHEMA_VERSION
    content_mode: str = "full"


@dataclass(frozen=True)
class RagDocument:
    id: str
    text: str


@dataclass(frozen=True)
class RagQuestion:
    id: str
    question: str
    context_ids: list[str]
    expected_keywords: list[str] = field(default_factory=list)
    feature: str | None = None
    workflow: str | None = None
    environment: str | None = None
    prompt_version: str | None = None


@dataclass(frozen=True)
class RagResult:
    question_id: str
    model_id: str
    response: str | None
    retrieved_context_tokens: int
    answer_tokens: int
    latency_ms: int
    estimated_cost_usd: float
    answer_coverage: float | None
    faithfulness_score: float | None
    context_efficiency: float | None
    unused_context_signal: float
    missing_citation: bool
    success: bool = True
    status: str = "success"
    error: str | None = None


@dataclass(frozen=True)
class RagReport:
    run_name: str
    description: str
    results: list[RagResult]
    schema_version: str = RAG_REPORT_SCHEMA_VERSION
    content_mode: str = "full"
