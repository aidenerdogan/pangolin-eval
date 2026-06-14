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
        data["models"][0]["token_counter"] = "whitespace"

        models = parse_models(data)

        self.assertEqual(models[0].max_retries, 2)
        self.assertEqual(models[0].token_counter, "whitespace")

    def test_parse_models_preserves_group_and_pricing_provenance(self) -> None:
        data = valid_config()
        data["models"][0]["model_group"] = "small"
        data["models"][0]["pricing_source"] = "catalog"
        data["models"][0]["pricing_source_url"] = "https://example.test/pricing"
        data["models"][0]["pricing_updated_at"] = "2026-06-13"
        data["models"][0]["price_override"] = True
        data["models"][0]["context_window_tokens"] = 8192
        data["models"][0]["supports_tools"] = True
        data["models"][0]["supports_json_mode"] = True
        data["models"][0]["latency_band"] = "low"

        validate_config(data)
        models = parse_models(data)

        self.assertEqual(models[0].model_group, "small")
        self.assertEqual(models[0].pricing_source, "catalog")
        self.assertTrue(models[0].extra["price_override"])
        self.assertEqual(models[0].context_window_tokens, 8192)
        self.assertTrue(models[0].supports_tools)
        self.assertTrue(models[0].supports_json_mode)
        self.assertEqual(models[0].latency_band, "low")

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

    def test_parse_prompts_preserves_evaluators(self) -> None:
        data = valid_config()
        data["prompts"][0]["evaluators"] = [
            {"type": "regex", "value": "refunds?", "weight": 2},
            {"type": "exact", "value": "refund policy", "case_sensitive": True},
        ]

        prompts = parse_prompts(data)

        self.assertEqual(prompts[0].evaluators[0].type, "regex")
        self.assertEqual(prompts[0].evaluators[0].weight, 2)
        self.assertTrue(prompts[0].evaluators[1].case_sensitive)

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

    def test_rejects_untrusted_openai_connection_config(self) -> None:
        data = valid_config()
        data["models"][0] = {
            "id": "live-model",
            "provider": "openai_compatible",
            "input_price_per_1m": 0.1,
            "output_price_per_1m": 0.2,
            "base_url": "http://example.test/v1",
            "api_key_env": "AWS_SECRET_ACCESS_KEY",
        }

        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            validate_config(data)

        data["models"][0]["base_url"] = "https://api.example.test/v1"
        with self.assertRaisesRegex(ValueError, "allow_unsafe_api_key_env"):
            validate_config(data)

    def test_allows_explicit_unsafe_api_key_env_opt_in(self) -> None:
        data = valid_config()
        data["models"][0] = {
            "id": "live-model",
            "provider": "openai_compatible",
            "input_price_per_1m": 0.1,
            "output_price_per_1m": 0.2,
            "base_url": "https://api.example.test/v1",
            "api_key_env": "CUSTOMER_SECRET_NAME",
            "allow_unsafe_api_key_env": True,
        }

        validate_config(data)
        self.assertTrue(parse_models(data)[0].extra["allow_unsafe_api_key_env"])

    def test_allows_loopback_http_provider_config(self) -> None:
        data = valid_config()
        data["models"][0] = {
            "id": "local-model",
            "provider": "openai_compatible",
            "input_price_per_1m": 0.1,
            "output_price_per_1m": 0.2,
            "base_url": "http://localhost:4000/v1",
            "api_key_env": "LITELLM_API_KEY",
        }

        validate_config(data)

    def test_rejects_known_api_key_env_for_unknown_host(self) -> None:
        for env_name in [
            "LITELLM_API_KEY",
            "OLLAMA_API_KEY",
            "OPENAI_API_KEY",
            "VLLM_API_KEY",
        ]:
            with self.subTest(env_name=env_name):
                data = valid_config()
                data["models"][0] = {
                    "id": "live-model",
                    "provider": "openai_compatible",
                    "input_price_per_1m": 0.1,
                    "output_price_per_1m": 0.2,
                    "base_url": "https://attacker.example/v1",
                    "api_key_env": env_name,
                }

                with self.assertRaisesRegex(ValueError, env_name):
                    validate_config(data)

    def test_allows_openai_api_key_for_openai_host(self) -> None:
        data = valid_config()
        data["models"][0] = {
            "id": "live-model",
            "provider": "openai_compatible",
            "input_price_per_1m": 0.1,
            "output_price_per_1m": 0.2,
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
        }

        validate_config(data)

    def test_rejects_negative_max_retries(self) -> None:
        data = valid_config()
        data["models"][0]["max_retries"] = -1

        with self.assertRaisesRegex(ValueError, "max_retries"):
            validate_config(data)

    def test_rejects_unknown_token_counter(self) -> None:
        data = valid_config()
        data["models"][0]["token_counter"] = "mystery"

        with self.assertRaisesRegex(ValueError, "unsupported token_counter"):
            validate_config(data)

    def test_rejects_invalid_evaluator(self) -> None:
        data = valid_config()
        data["prompts"][0]["evaluators"] = [{"type": "regex", "value": "["}]

        with self.assertRaisesRegex(ValueError, "invalid regex"):
            validate_config(data)

    def test_rejects_nested_quantifier_regex_evaluator(self) -> None:
        data = valid_config()
        data["prompts"][0]["evaluators"] = [{"type": "regex", "value": "(a+)+$"}]

        with self.assertRaisesRegex(ValueError, "nested quantifiers"):
            validate_config(data)

    def test_allows_non_capturing_group_regex_evaluator(self) -> None:
        data = valid_config()
        data["prompts"][0]["evaluators"] = [
            {"type": "regex", "value": "(?:refund|return)+"}
        ]

        validate_config(data)

    def test_allows_literal_brace_regex_evaluator(self) -> None:
        data = valid_config()
        data["prompts"][0]["evaluators"] = [
            {"type": "regex", "value": r"(foo{bar})+"}
        ]

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
