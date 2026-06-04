from __future__ import annotations

import copy
import unittest

from pangolin_eval.config import parse_models, validate_config


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


if __name__ == "__main__":
    unittest.main()
