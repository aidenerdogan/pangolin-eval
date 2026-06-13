from __future__ import annotations

import copy
import unittest

from pangolin_eval.config import parse_gates, parse_models, parse_prompts, validate_config


def valid_config() -> dict[str, object]:
    return {
        "run_name": "test-run",
        "models": [
            {
                "id": "mock-model",
                "provider": "mock",
                "input_price_per_1m": 0.1,
                "output_price_per_1m": 0.2,
                "mock_latency_ms": 25,
                "mock_responses": {"case-1": "refund policy"},
            }
        ],
        "prompts": [
            {
                "id": "case-1",
                "messages": [{"role": "user", "content": "What should support do?"}],
                "expected_keywords": ["refund", "policy"],
            }
        ],
    }


class ConfigValidationTest(unittest.TestCase):
    def test_valid_config_passes(self) -> None:
        validate_config(valid_config())

    def test_parse_models_preserves_provider_specific_fields(self) -> None:
        data = valid_config()

        models = parse_models(data)

        self.assertEqual(models[0].mock_latency_ms, 25)
        self.assertEqual(models[0].extra["mock_responses"]["case-1"], "refund policy")

    def test_parse_models_preserves_retry_config(self) -> None:
        data = valid_config()
        data["models"][0]["max_retries"] = 2

        models = parse_models(data)

        self.assertEqual(models[0].max_retries, 2)

    def test_parse_models_preserves_group_and_pricing_provenance(self) -> None:
        data = valid_config()
        data["models"][0]["model_group"] = "small"
        data["models"][0]["pricing_source"] = "catalog"
        data["models"][0]["pricing_source_url"] = "https://example.test/pricing"
        data["models"][0]["pricing_updated_at"] = "2026-06-13"
        data["models"][0]["price_override"] = True

        validate_config(data)
        models = parse_models(data)

        self.assertEqual(models[0].model_group, "small")
        self.assertEqual(models[0].pricing_source, "catalog")
        self.assertTrue(models[0].extra["price_override"])

    def test_parse_prompts_preserves_attribution_fields(self) -> None:
        data = valid_config()
        data["prompts"][0]["feature"] = "support"
        data["prompts"][0]["workflow"] = "refund"
        data["prompts"][0]["environment"] = "test"
        data["prompts"][0]["prompt_version"] = "v1"
        data["prompts"][0]["customer_user_hash"] = "user-hash"

        prompts = parse_prompts(data)

        self.assertEqual(prompts[0].feature, "support")
        self.assertEqual(prompts[0].workflow, "refund")
        self.assertEqual(prompts[0].customer_user_hash, "user-hash")

    def test_parse_gates_returns_thresholds(self) -> None:
        data = valid_config()
        data["gates"] = {
            "max_total_cost_usd": 0.01,
            "min_success_rate": 1.0,
        }

        validate_config(data)

        self.assertEqual(
            parse_gates(data),
            {"max_total_cost_usd": 0.01, "min_success_rate": 1.0},
        )

    def test_rejects_duplicate_model_ids(self) -> None:
        data = valid_config()
        data["models"] = copy.deepcopy(data["models"]) + copy.deepcopy(data["models"])

        with self.assertRaisesRegex(ValueError, "Model id 'mock-model' must be unique"):
            validate_config(data)

    def test_rejects_message_without_content(self) -> None:
        data = valid_config()
        data["prompts"][0]["messages"] = [{"role": "user"}]

        with self.assertRaisesRegex(
            ValueError,
            "Prompt case-1 message 1 field 'content'",
        ):
            validate_config(data)

    def test_rejects_openai_compatible_without_credentials_config(self) -> None:
        data = valid_config()
        data["models"][0] = {
            "id": "live-model",
            "provider": "openai_compatible",
            "input_price_per_1m": 0.1,
            "output_price_per_1m": 0.2,
            "base_url": "https://api.example.test/v1",
        }

        with self.assertRaisesRegex(ValueError, "field 'api_key_env'"):
            validate_config(data)

    def test_rejects_negative_max_retries(self) -> None:
        data = valid_config()
        data["models"][0]["max_retries"] = -1

        with self.assertRaisesRegex(ValueError, "max_retries"):
            validate_config(data)

    def test_rejects_unknown_gate(self) -> None:
        data = valid_config()
        data["gates"] = {"max_surprise": 1}

        with self.assertRaisesRegex(ValueError, "Gate 'max_surprise' is not supported"):
            validate_config(data)

    def test_rejects_probability_gate_above_one(self) -> None:
        data = valid_config()
        data["gates"] = {"min_success_rate": 1.1}

        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            validate_config(data)


if __name__ == "__main__":
    unittest.main()
