# pangolin-eval

Measure and compare LLM, RAG, and agent workloads across cost, latency, quality, and reliability.

`pangolin-eval` is an open-source toolkit for AI product teams, startup CTOs, and senior engineers who need to understand which model is good enough before inference cost becomes painful. It helps teams run structured prompt or workflow evaluations, estimate cost, track latency, and generate decision-ready reports.

## Why This Exists

AI products are no longer judged only by answer quality. In production, the useful question is:

> Which model gives enough quality for this task at an acceptable cost, latency, and reliability?

This project starts with local, file-based workflows:

- compare models on the same prompts
- estimate token and provider cost
- measure latency
- score weighted quality checks
- generate Markdown, JSON, and optional static HTML reports
- apply budget, quality, latency, and reliability gates
- summarize attribution by model, prompt, feature, workflow, environment, and prompt version
- evaluate synthetic RAG tasks for context efficiency and answer coverage
- generate agent/workflow TraceCards from local trace events
- produce auditable recommendations and OTel-style exports

## Quickstart

Run the bundled mock comparison. It does not require API keys.

```bash
cd pangolin-eval
PYTHONPATH=src python -m pangolin_eval.cli run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare \
  --html
```

For sensitive runs, omit response text from saved artifacts while keeping metrics and quality scores:

```bash
PYTHONPATH=src python -m pangolin_eval.cli run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare_private \
  --content-mode metadata-only
```

Open the generated report:

```bash
cat reports/simple_model_compare/report.md
```

Validate a config without running providers:

```bash
PYTHONPATH=src python -m pangolin_eval.cli validate \
  --config examples/simple_model_compare/config.json
```

Run the synthetic RAG evaluation:

```bash
PYTHONPATH=src python -m pangolin_eval.cli rag \
  --config examples/rag_eval/config.json \
  --out reports/rag_eval \
  --content-mode metadata-only
```

Generate agent/workflow TraceCards from local trace events:

```bash
PYTHONPATH=src python -m pangolin_eval.cli trace \
  --input examples/agent_trace/trace_events.json \
  --out reports/agent_trace
```

Export supported artifacts as OTel-style spans:

```bash
PYTHONPATH=src python -m pangolin_eval.cli export-otel \
  --input reports/simple_model_compare/report.json \
  --out reports/simple_model_compare/otel.json
```

Install locally for CLI usage:

```bash
python -m pip install -e .
pangolin-eval run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare
```

## Example Output

The report ranks models by a simple efficiency score that combines quality, cost, and latency.

```text
| Model | Runs | Success rate | Avg quality | Avg latency ms | Estimated cost USD | Recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| fast-cheap | 2 | 1.00 | 1.00 | 180 | 0.00006015 | Best quality candidate |
| balanced | 2 | 1.00 | 1.00 | 320 | 0.00022060 | Best quality candidate |
| strong-expensive | 2 | 1.00 | 1.00 | 540 | 0.00127250 | Usable with latency review |
```

## Current Scope

The current local open-source version includes:

- Python 3.9+ CLI and library
- config-driven model and prompt comparison
- mock provider for reproducible public demos
- OpenAI-compatible provider adapter
- latency, token, and cost tracking
- keyword, contains, regex, and exact-match quality evaluators
- configurable token counters for estimated usage fallback
- Markdown, JSON, and optional static HTML reporting
- versioned report schema
- metadata-only report mode for privacy-conscious runs
- budget, quality, latency, and reliability gates
- failure-tolerant runs with success/error status fields
- attribution and pricing provenance summaries
- synthetic RAG evaluation CLI and report with context diagnostics
- local agent/workflow TraceCards with loop and waste diagnostics
- auditable recommendations-lite
- OTel-style export for reports and TraceCards
- OpenAI-compatible, LiteLLM, Ollama, and vLLM gateway examples
- Docker Compose no-key demos

## Project Status

Latest release: `v0.2.2`.

The planned local open-source scope is implemented for the current release track:
weighted evaluator plugins, configurable token counters, additional gateway examples,
RAG and agent diagnostics, and optional static HTML reports are available. Future work
can focus on polish, more adapters, and hosted or team workflows without weakening the
local CLI/library foundation.

## Report Contract

JSON reports declare a schema version and content mode:

- `schema_version`: currently `pangolin-eval.report.v4`
- `content_mode`: `full` or `metadata_only`

See [docs/REPORT_SCHEMA.md](docs/REPORT_SCHEMA.md), [docs/EXTENSIONS.md](docs/EXTENSIONS.md), [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md), [docs/MIGRATIONS.md](docs/MIGRATIONS.md), [docs/RELEASE.md](docs/RELEASE.md), and the files under [schemas/](schemas).

## Support And Feedback

Use [SUPPORT.md](SUPPORT.md) for the best path to ask questions, report bugs, or suggest integrations.
See [docs/LAUNCH.md](docs/LAUNCH.md) for launch notes, suggested demo flows, and copy that explains the project clearly.

## Local Demo With Docker

```bash
docker compose run --rm demo
docker compose run --rm rag-demo
```

## Open-Core Direction

This repo is the public CLI/library foundation. Commercial extensions may build on top of this engine for UI, run history, team workflows, recommendations, alerts, and executive reports.

The open-source project should remain useful on its own: local reports, transparent metrics, reproducible examples, and CI-friendly gates stay public.

## Configuration

See [examples/simple_model_compare/config.json](examples/simple_model_compare/config.json).

Top-level config can include:

- `run_name`: report title
- `description`: report description
- `pricing_catalog`: optional relative path to a pricing catalog
- `gates`: optional cost, quality, latency, and reliability thresholds

Model entries include:

- `id`: display name used in reports
- `provider`: `mock` or `openai_compatible`
- `api_model`: provider model id, if different from `id`
- `input_price_per_1m`: input token cost estimate
- `output_price_per_1m`: output token cost estimate
- `model_group`: optional grouping for attribution
- `max_retries`: retry attempts after provider failures
- `token_counter`: estimated usage fallback, one of `char_4`, `whitespace`, or `openai_chat`
- `pricing_source`, `pricing_source_url`, `pricing_updated_at`: pricing provenance
- capability metadata such as `context_window_tokens`, `supports_tools`, `supports_json_mode`, and `latency_band`
- `allow_unsafe_api_key_env`: opt-in escape hatch for custom API key environment variable names or non-default provider hosts; by default OpenAI-compatible configs only allow known safe API key/host pairings or the `PANGOLIN_EVAL_` prefix, and `base_url` must use HTTPS unless it points to loopback

Prompt entries include:

- `id`: prompt case identifier
- `messages`: chat-style messages
- `expected_keywords`: optional simple quality check
- `evaluators`: optional weighted checks using `keyword`, `contains`, `regex`, or `exact`
- attribution fields such as `feature`, `workflow`, `environment`, `prompt_version`, and `customer_user_hash`

Evaluator example:

```json
{
  "evaluators": [
    {"type": "contains", "value": "latency"},
    {"type": "regex", "value": "cost|price|spend", "weight": 2}
  ]
}
```

Regex evaluators are intentionally constrained: patterns must be at most 256
characters and nested quantifiers are rejected to avoid excessive runtime on
untrusted responses.

Gate examples:

```json
{
  "gates": {
    "max_total_cost_usd": 0.01,
    "max_avg_latency_ms": 500,
    "min_avg_quality": 0.75,
    "min_success_rate": 1.0
  }
}
```

## OpenAI-Compatible Providers

To use a real provider, configure a model with `provider: "openai_compatible"` and set an API key environment variable.

```json
{
  "id": "gpt-4o-mini",
  "provider": "openai_compatible",
  "api_model": "gpt-4o-mini",
  "base_url": "https://api.openai.com/v1",
  "api_key_env": "OPENAI_API_KEY",
  "input_price_per_1m": 0.15,
  "output_price_per_1m": 0.6
}
```

Then run:

```bash
export OPENAI_API_KEY="..."
pangolin-eval run --config path/to/config.json --out reports/live
```

Additional templates:

- [examples/ci_gate/config.json](examples/ci_gate/config.json)
- [examples/openai_compatible/config.json](examples/openai_compatible/config.json)
- [examples/litellm_gateway/config.json](examples/litellm_gateway/config.json)
- [examples/ollama_openai_compatible/config.json](examples/ollama_openai_compatible/config.json)
- [examples/vllm_openai_compatible/config.json](examples/vllm_openai_compatible/config.json)

## Intended Users

- AI product teams comparing model tradeoffs
- startup CTOs controlling AI product cost
- senior AI engineers building production LLM systems
- ML platform engineers supporting LLMOps workflows

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## License

MIT
