from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pangolin_eval.models import (
    SUPPORTED_EVALUATOR_TYPES,
    SUPPORTED_TOKEN_COUNTERS,
    ModelTarget,
    PromptCase,
    QualityEvaluator,
)
from pangolin_eval.safety import validate_openai_connection_security

SUPPORTED_PROVIDERS = {"mock", "openai_compatible"}
SUPPORTED_GATES = {
    "max_total_cost_usd",
    "max_prompt_cost_usd",
    "max_avg_latency_ms",
    "max_latency_ms",
    "min_avg_quality",
    "min_success_rate",
}


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Config file {config_path} is not valid JSON: "
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}."
            ) from exc
    validate_config(data)
    return data


def validate_config(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object.")

    models = _required_non_empty_list(data, "models", "Config")
    prompts = _required_non_empty_list(data, "prompts", "Config")

    _validate_optional_string(data, "run_name", "Config")
    _validate_optional_string(data, "description", "Config")
    _validate_optional_string(data, "pricing_catalog", "Config")
    _validate_unique_ids(models, "Model")
    _validate_unique_ids(prompts, "Prompt")
    if "gates" in data:
        _validate_gates(data["gates"])

    for model in models:
        if not isinstance(model, dict):
            raise ValueError("Each model config must be an object.")
        required = ["id", "provider", "input_price_per_1m", "output_price_per_1m"]
        missing = [name for name in required if name not in model]
        if missing:
            raise ValueError(
                f"Model config is missing fields: {', '.join(missing)}."
            )

        model_id = _require_string(model, "id", "Model")
        provider = _require_string(model, "provider", f"Model {model_id}")
        if provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise ValueError(
                f"Model {model_id} has unsupported provider '{provider}'. "
                f"Supported providers: {supported}."
            )
        _require_non_negative_number(
            model,
            "input_price_per_1m",
            f"Model {model_id}",
        )
        _require_non_negative_number(
            model,
            "output_price_per_1m",
            f"Model {model_id}",
        )
        _validate_optional_string(model, "api_model", f"Model {model_id}")
        _validate_optional_string(model, "base_url", f"Model {model_id}")
        _validate_optional_string(model, "api_key_env", f"Model {model_id}")
        _validate_optional_string(model, "mock_response", f"Model {model_id}")
        _validate_optional_string(model, "model_group", f"Model {model_id}")
        _validate_optional_string(model, "pricing_source", f"Model {model_id}")
        _validate_optional_string(model, "pricing_source_url", f"Model {model_id}")
        _validate_optional_string(model, "pricing_updated_at", f"Model {model_id}")
        _validate_optional_string(model, "latency_band", f"Model {model_id}")
        if "token_counter" in model:
            token_counter = _require_string(model, "token_counter", f"Model {model_id}")
            if token_counter not in SUPPORTED_TOKEN_COUNTERS:
                supported = ", ".join(sorted(SUPPORTED_TOKEN_COUNTERS))
                raise ValueError(
                    f"Model {model_id} has unsupported token_counter "
                    f"'{token_counter}'. Supported counters: {supported}."
                )

        if "mock_latency_ms" in model:
            _require_non_negative_number(model, "mock_latency_ms", f"Model {model_id}")
        if "max_retries" in model:
            _require_non_negative_integer(model, "max_retries", f"Model {model_id}")
        if "context_window_tokens" in model:
            _require_non_negative_integer(
                model,
                "context_window_tokens",
                f"Model {model_id}",
            )
        if "price_override" in model:
            _require_bool(model, "price_override", f"Model {model_id}")
        if "allow_unsafe_api_key_env" in model:
            _require_bool(model, "allow_unsafe_api_key_env", f"Model {model_id}")
        for field in [
            "supports_tools",
            "supports_structured_output",
            "supports_json_mode",
            "supports_multimodal",
        ]:
            if field in model:
                _require_bool(model, field, f"Model {model_id}")
        if "mock_responses" in model:
            _validate_mock_responses(model["mock_responses"], model_id)
        if provider == "openai_compatible":
            base_url = _require_string(model, "base_url", f"Model {model_id}")
            api_key_env = _require_string(model, "api_key_env", f"Model {model_id}")
            validate_openai_connection_security(
                base_url=base_url,
                api_key_env=api_key_env,
                owner=f"Model {model_id}",
                allow_unsafe_api_key_env=model.get("allow_unsafe_api_key_env") is True,
            )

    for prompt in prompts:
        if not isinstance(prompt, dict):
            raise ValueError("Each prompt config must be an object.")
        if "id" not in prompt or "messages" not in prompt:
            raise ValueError("Each prompt must include 'id' and 'messages'.")
        prompt_id = _require_string(prompt, "id", "Prompt")
        messages = _required_non_empty_list(prompt, "messages", f"Prompt {prompt_id}")
        for index, message in enumerate(messages, start=1):
            _validate_message(message, prompt_id, index)
        if "expected_keywords" in prompt:
            _validate_string_list(
                prompt["expected_keywords"],
                "expected_keywords",
                f"Prompt {prompt_id}",
            )
        if "evaluators" in prompt:
            _validate_evaluators(prompt["evaluators"], f"Prompt {prompt_id}")
        for field in [
            "feature",
            "workflow",
            "environment",
            "prompt_version",
            "customer_user_hash",
        ]:
            _validate_optional_string(prompt, field, f"Prompt {prompt_id}")


def parse_models(data: dict[str, Any]) -> list[ModelTarget]:
    models: list[ModelTarget] = []
    known_fields = {
        "id",
        "provider",
        "input_price_per_1m",
        "output_price_per_1m",
        "api_model",
        "base_url",
        "api_key_env",
        "mock_latency_ms",
        "mock_response",
        "max_retries",
        "model_group",
        "pricing_source",
        "pricing_source_url",
        "pricing_updated_at",
        "context_window_tokens",
        "supports_tools",
        "supports_structured_output",
        "supports_json_mode",
        "supports_multimodal",
        "latency_band",
        "token_counter",
    }
    for raw in data["models"]:
        extra = {key: value for key, value in raw.items() if key not in known_fields}
        models.append(
            ModelTarget(
                id=raw["id"],
                provider=raw["provider"],
                input_price_per_1m=float(raw["input_price_per_1m"]),
                output_price_per_1m=float(raw["output_price_per_1m"]),
                api_model=raw.get("api_model"),
                base_url=raw.get("base_url"),
                api_key_env=raw.get("api_key_env"),
                mock_latency_ms=raw.get("mock_latency_ms"),
                mock_response=raw.get("mock_response"),
                max_retries=int(raw.get("max_retries", 0)),
                model_group=raw.get("model_group"),
                pricing_source=raw.get("pricing_source", "manual"),
                pricing_source_url=raw.get("pricing_source_url"),
                pricing_updated_at=raw.get("pricing_updated_at"),
                context_window_tokens=raw.get("context_window_tokens"),
                supports_tools=bool(raw.get("supports_tools", False)),
                supports_structured_output=bool(raw.get("supports_structured_output", False)),
                supports_json_mode=bool(raw.get("supports_json_mode", False)),
                supports_multimodal=bool(raw.get("supports_multimodal", False)),
                latency_band=raw.get("latency_band"),
                token_counter=raw.get("token_counter", "char_4"),
                extra=extra,
            )
        )
    return models


def parse_prompts(data: dict[str, Any]) -> list[PromptCase]:
    prompts: list[PromptCase] = []
    for raw in data["prompts"]:
        prompts.append(
            PromptCase(
                id=raw["id"],
                messages=raw["messages"],
                expected_keywords=list(raw.get("expected_keywords", [])),
                evaluators=parse_evaluators(raw.get("evaluators", [])),
                feature=raw.get("feature"),
                workflow=raw.get("workflow"),
                environment=raw.get("environment"),
                prompt_version=raw.get("prompt_version"),
                customer_user_hash=raw.get("customer_user_hash"),
            )
        )
    return prompts


def parse_evaluators(raw_evaluators: list[dict[str, Any]]) -> list[QualityEvaluator]:
    return [
        QualityEvaluator(
            type=evaluator["type"],
            value=evaluator["value"],
            weight=float(evaluator.get("weight", 1.0)),
            case_sensitive=bool(evaluator.get("case_sensitive", False)),
        )
        for evaluator in raw_evaluators
    ]


def parse_gates(data: dict[str, Any]) -> dict[str, float]:
    gates = data.get("gates", {})
    return {name: float(value) for name, value in gates.items()}


def _required_non_empty_list(
    data: dict[str, Any],
    field: str,
    owner: str,
) -> list[Any]:
    value = data.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{owner} must include a non-empty '{field}' list.")
    return value


def _validate_unique_ids(items: list[Any], owner: str) -> None:
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            continue
        item_id = item["id"]
        if not isinstance(item_id, str):
            continue
        if item_id in seen:
            raise ValueError(f"{owner} id '{item_id}' must be unique.")
        seen.add(item_id)


def _require_string(data: dict[str, Any], field: str, owner: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} field '{field}' must be a non-empty string.")
    return value


def _validate_optional_string(data: dict[str, Any], field: str, owner: str) -> None:
    if field in data and data[field] is not None:
        _require_string(data, field, owner)


def _require_non_negative_number(
    data: dict[str, Any],
    field: str,
    owner: str,
) -> float:
    value = data.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{owner} field '{field}' must be a non-negative number.")
    return float(value)


def _require_non_negative_integer(
    data: dict[str, Any],
    field: str,
    owner: str,
) -> int:
    value = data.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{owner} field '{field}' must be a non-negative integer.")
    return value


def _require_bool(data: dict[str, Any], field: str, owner: str) -> bool:
    value = data.get(field)
    if not isinstance(value, bool):
        raise ValueError(f"{owner} field '{field}' must be a boolean.")
    return value


def _validate_gates(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("Config field 'gates' must be an object.")
    for name, threshold in value.items():
        if name not in SUPPORTED_GATES:
            supported = ", ".join(sorted(SUPPORTED_GATES))
            raise ValueError(
                f"Gate '{name}' is not supported. Supported gates: {supported}."
            )
        _require_non_negative_number(value, name, "Config gates")
        if name in {"min_avg_quality", "min_success_rate"} and value[name] > 1:
            raise ValueError(
                f"Config gates field '{name}' must be between 0 and 1."
            )


def _validate_mock_responses(value: Any, model_id: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"Model {model_id} field 'mock_responses' must be an object.")
    for prompt_id, response in value.items():
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            raise ValueError(
                f"Model {model_id} field 'mock_responses' keys must be strings."
            )
        if not isinstance(response, str):
            raise ValueError(
                f"Model {model_id} mock response for '{prompt_id}' must be a string."
            )


def _validate_message(message: Any, prompt_id: str, index: int) -> None:
    if not isinstance(message, dict):
        raise ValueError(f"Prompt {prompt_id} message {index} must be an object.")
    _require_string(message, "role", f"Prompt {prompt_id} message {index}")
    _require_string(message, "content", f"Prompt {prompt_id} message {index}")


def _validate_string_list(value: Any, field: str, owner: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{owner} field '{field}' must be a list of strings.")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{owner} field '{field}' must contain only strings.")


def _validate_evaluators(value: Any, owner: str) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{owner} field 'evaluators' must be a non-empty list.")
    for index, evaluator in enumerate(value, start=1):
        evaluator_owner = f"{owner} evaluator {index}"
        if not isinstance(evaluator, dict):
            raise ValueError(f"{evaluator_owner} must be an object.")
        evaluator_type = _require_string(evaluator, "type", evaluator_owner)
        if evaluator_type not in SUPPORTED_EVALUATOR_TYPES:
            supported = ", ".join(sorted(SUPPORTED_EVALUATOR_TYPES))
            raise ValueError(
                f"{evaluator_owner} has unsupported type '{evaluator_type}'. "
                f"Supported evaluator types: {supported}."
            )
        evaluator_value = _require_string(evaluator, "value", evaluator_owner)
        if evaluator_type == "regex":
            try:
                re.compile(evaluator_value)
            except re.error as exc:
                raise ValueError(
                    f"{evaluator_owner} has invalid regex: {exc}."
                ) from exc
            _validate_safe_regex(evaluator_value, evaluator_owner)
        if "weight" in evaluator:
            weight = _require_non_negative_number(evaluator, "weight", evaluator_owner)
            if weight == 0:
                raise ValueError(f"{evaluator_owner} field 'weight' must be positive.")
        if "case_sensitive" in evaluator:
            _require_bool(evaluator, "case_sensitive", evaluator_owner)


def _validate_safe_regex(pattern: str, owner: str) -> None:
    if len(pattern) > 256:
        raise ValueError(f"{owner} regex must be 256 characters or fewer.")
    if _contains_nested_quantifier(pattern):
        raise ValueError(
            f"{owner} regex contains nested quantifiers that can cause excessive runtime."
        )


def _contains_nested_quantifier(pattern: str) -> bool:
    in_class = False
    escaped = False
    group_syntax_until = 0
    group_has_quantifier: list[bool] = []

    for index, char in enumerate(pattern):
        if index < group_syntax_until:
            continue
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "[":
            in_class = True
            continue
        if char == "]":
            in_class = False
            continue
        if in_class:
            continue
        if char == "(":
            group_has_quantifier.append(False)
            if pattern[index + 1 : index + 2] == "?":
                group_syntax_until = _group_syntax_end(pattern, index)
            continue
        if char in "*+?" or (char == "{" and _starts_repetition_quantifier(pattern, index)):
            if group_has_quantifier:
                group_has_quantifier[-1] = True
            continue
        if char == ")" and group_has_quantifier:
            inner_has_quantifier = group_has_quantifier.pop()
            if not inner_has_quantifier:
                continue
            next_char = pattern[index + 1 : index + 2]
            if next_char in {"*", "+", "?", "{"}:
                return True
            if group_has_quantifier:
                group_has_quantifier[-1] = True
    return False


def _starts_repetition_quantifier(pattern: str, open_index: int) -> bool:
    index = open_index + 1
    if index >= len(pattern) or not pattern[index].isdigit():
        return False
    while index < len(pattern) and pattern[index].isdigit():
        index += 1
    if index < len(pattern) and pattern[index] == ",":
        index += 1
        while index < len(pattern) and pattern[index].isdigit():
            index += 1
    return index < len(pattern) and pattern[index] == "}"


def _group_syntax_end(pattern: str, open_index: int) -> int:
    if pattern[open_index + 1 : open_index + 2] != "?":
        return open_index + 1
    if pattern[open_index + 2 : open_index + 3] in {":", "=", "!"}:
        return open_index + 3
    if pattern[open_index + 2 : open_index + 3] == "<":
        if pattern[open_index + 3 : open_index + 4] in {"=", "!"}:
            return open_index + 4
        close_index = pattern.find(">", open_index + 3)
        if close_index != -1:
            return close_index + 1
    return open_index + 1
