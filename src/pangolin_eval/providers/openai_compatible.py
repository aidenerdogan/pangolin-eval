from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from pangolin_eval.models import Completion, ModelTarget, PromptCase
from pangolin_eval.providers.base import Provider
from pangolin_eval.scoring import estimate_message_tokens, estimate_tokens


class OpenAICompatibleProvider(Provider):
    def complete(self, model: ModelTarget, prompt: PromptCase) -> Completion:
        if not model.base_url:
            raise ValueError(f"Model {model.id} requires 'base_url'.")
        if not model.api_key_env:
            raise ValueError(f"Model {model.id} requires 'api_key_env'.")

        api_key = os.environ.get(model.api_key_env)
        if not api_key:
            raise ValueError(
                f"Environment variable {model.api_key_env} is not set for model {model.id}."
            )

        payload = {
            "model": model.api_model or model.id,
            "messages": prompt.messages,
        }
        body = json.dumps(payload).encode("utf-8")
        endpoint = model.base_url.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Provider returned HTTP {exc.code}: {message}") from exc

        latency_ms = round((time.perf_counter() - started) * 1000)
        data = json.loads(raw)
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        usage_source = "provider" if usage else "estimated"

        return Completion(
            text=text,
            input_tokens=int(usage.get("prompt_tokens") or estimate_message_tokens(prompt.messages)),
            output_tokens=int(usage.get("completion_tokens") or estimate_tokens(text)),
            latency_ms=latency_ms,
            metadata={
                "provider": "openai_compatible",
                "api_model": model.api_model or model.id,
                "usage": usage,
            },
            usage_source=usage_source,
        )
