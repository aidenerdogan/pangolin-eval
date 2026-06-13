from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pangolin_eval.models import ModelTarget, PromptCase

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

        if "mock_latency_ms" in model:
            _require_non_negative_number(model, "mock_latency_ms", f"Model {model_id}")
        if "max_retries" in model:
            _require_non_negative_integer(model, "max_retries", f"Model {model_id}")
        if "price_override" in model:
            _require_bool(model, "price_override", f"Model {model_id}")
        if "mock_responses" in model:
            _validate_mock_responses(model["mock_responses"], model_id)
        if provider == "openai_compatible":
            _require_string(model, "base_url", f"Model {model_id}")
            _require_string(model, "api_key_env", f"Model {model_id}")

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
                feature=raw.get("feature"),
                workflow=raw.get("workflow"),
                environment=raw.get("environment"),
                prompt_version=raw.get("prompt_version"),
                customer_user_hash=raw.get("customer_user_hash"),
            )
        )
    return prompts


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
