from __future__ import annotations

import io
import json
import os
import urllib.error
import unittest
from unittest.mock import patch

from pangolin_eval.models import ModelTarget, PromptCase
from pangolin_eval.providers.openai_compatible import OpenAICompatibleProvider


class FakeResponse:
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {
                "choices": [{"message": {"content": "Use the refund policy."}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 5},
            }
        ).encode("utf-8")


class OpenAICompatibleProviderTest(unittest.TestCase):
    def test_complete_posts_chat_request_and_uses_provider_usage(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request: object, timeout: int) -> FakeResponse:
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["authorization"] = request.headers["Authorization"]
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        model = ModelTarget(
            id="example-model",
            provider="openai_compatible",
            api_model="provider-model",
            base_url="https://api.example.test/v1/",
            api_key_env="PANGOLIN_EVAL_TEST_KEY",
            input_price_per_1m=0.1,
            output_price_per_1m=0.2,
        )
        prompt = PromptCase(
            id="case-1",
            messages=[{"role": "user", "content": "What should support do?"}],
        )

        with patch.dict(os.environ, {"PANGOLIN_EVAL_TEST_KEY": "test-key"}):
            with patch(
                "pangolin_eval.providers.openai_compatible.urllib.request.urlopen",
                fake_urlopen,
            ):
                completion = OpenAICompatibleProvider().complete(model, prompt)

        self.assertEqual(captured["url"], "https://api.example.test/v1/chat/completions")
        self.assertEqual(captured["timeout"], 60)
        self.assertEqual(captured["authorization"], "Bearer test-key")
        self.assertEqual(captured["payload"]["model"], "provider-model")
        self.assertEqual(completion.text, "Use the refund policy.")
        self.assertEqual(completion.input_tokens, 7)
        self.assertEqual(completion.output_tokens, 5)
        self.assertEqual(completion.metadata["provider"], "openai_compatible")

    def test_complete_preserves_provider_reported_zero_usage(self) -> None:
        captured: dict[str, object] = {}

        class ZeroUsageResponse(FakeResponse):
            def read(self) -> bytes:
                return json.dumps(
                    {
                        "choices": [{"message": {"content": ""}}],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                    }
                ).encode("utf-8")

        def fake_urlopen(request: object, timeout: int) -> ZeroUsageResponse:
            captured["url"] = request.full_url
            return ZeroUsageResponse()

        model = ModelTarget(
            id="example-model",
            provider="openai_compatible",
            base_url="https://api.example.test/v1/",
            api_key_env="PANGOLIN_EVAL_TEST_KEY",
            input_price_per_1m=0.1,
            output_price_per_1m=0.2,
        )
        prompt = PromptCase(
            id="case-1",
            messages=[{"role": "user", "content": "What should support do?"}],
        )

        with patch.dict(os.environ, {"PANGOLIN_EVAL_TEST_KEY": "test-key"}):
            with patch(
                "pangolin_eval.providers.openai_compatible.urllib.request.urlopen",
                fake_urlopen,
            ):
                completion = OpenAICompatibleProvider().complete(model, prompt)

        self.assertEqual(captured["url"], "https://api.example.test/v1/chat/completions")
        self.assertEqual(completion.input_tokens, 0)
        self.assertEqual(completion.output_tokens, 0)

    def test_http_error_does_not_include_provider_body(self) -> None:
        def fake_urlopen(request: object, timeout: int) -> FakeResponse:
            body = io.BytesIO(b'{"error":"SECRET_PROMPT"}')
            raise urllib.error.HTTPError(
                request.full_url,
                400,
                "Bad Request",
                {},
                body,
            )

        model = ModelTarget(
            id="example-model",
            provider="openai_compatible",
            base_url="https://api.example.test/v1/",
            api_key_env="PANGOLIN_EVAL_TEST_KEY",
            input_price_per_1m=0.1,
            output_price_per_1m=0.2,
        )
        prompt = PromptCase(
            id="case-1",
            messages=[{"role": "user", "content": "What should support do?"}],
        )

        with patch.dict(os.environ, {"PANGOLIN_EVAL_TEST_KEY": "test-key"}):
            with patch(
                "pangolin_eval.providers.openai_compatible.urllib.request.urlopen",
                fake_urlopen,
            ):
                with self.assertRaisesRegex(RuntimeError, "HTTP 400") as caught:
                    OpenAICompatibleProvider().complete(model, prompt)
        self.assertNotIn("SECRET_PROMPT", str(caught.exception))

    def test_rejects_unsafe_direct_model_connection(self) -> None:
        model = ModelTarget(
            id="example-model",
            provider="openai_compatible",
            base_url="https://api.example.test/v1/",
            api_key_env="AWS_SECRET_ACCESS_KEY",
            input_price_per_1m=0.1,
            output_price_per_1m=0.2,
        )
        prompt = PromptCase(id="case-1", messages=[{"role": "user", "content": "Hi"}])

        with self.assertRaisesRegex(ValueError, "allow_unsafe_api_key_env"):
            OpenAICompatibleProvider().complete(model, prompt)

    def test_rejects_known_secret_for_unknown_direct_host(self) -> None:
        model = ModelTarget(
            id="example-model",
            provider="openai_compatible",
            base_url="https://attacker.example/v1/",
            api_key_env="OPENAI_API_KEY",
            input_price_per_1m=0.1,
            output_price_per_1m=0.2,
        )
        prompt = PromptCase(id="case-1", messages=[{"role": "user", "content": "Hi"}])

        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            OpenAICompatibleProvider().complete(model, prompt)


if __name__ == "__main__":
    unittest.main()
