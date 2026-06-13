# pangolin-eval

Measure and compare LLM, RAG, and agent workloads across cost, latency, quality, and reliability.

`pangolin-eval` is an open-source toolkit for AI product teams, startup CTOs, and senior engineers who need to understand which model is good enough before inference cost becomes painful. It helps teams run structured prompt or workflow evaluations, estimate cost, track latency, and generate decision-ready reports.

## Why This Exists

AI products are no longer judged only by answer quality. In production, the useful question is:

> Which model gives enough quality for this task at an acceptable cost, latency, and reliability?

This project starts with a focused workflow:

- compare models on the same prompts
- estimate token and provider cost
- measure latency
- score simple quality checks
- generate Markdown and JSON reports

Future versions will extend this into RAG evaluation, agent workflow tracing, model routing recommendations, and budget guardrails.

## Quickstart

Run the bundled mock comparison. It does not require API keys.

```bash
cd pangolin-eval
PYTHONPATH=src python -m pangolin_eval.cli run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare
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
| Model | Avg quality | Avg latency ms | Estimated cost USD | Recommendation |
| --- | ---: | ---: | ---: | --- |
| fast-cheap | 0.83 | 180 | 0.000001 | Good baseline |
| strong-expensive | 1.00 | 540 | 0.000014 | Best quality |
```

## Current Scope

Version 0.1 focuses on the smallest useful artifact:

- Python 3.9+ CLI and library
- config-driven model and prompt comparison
- mock provider for reproducible public demos
- OpenAI-compatible provider adapter
- latency, token, and cost tracking
- keyword-based quality scoring
- Markdown and JSON reporting
- versioned report schema
- metadata-only report mode for privacy-conscious runs

## Planned Scope

- LiteLLM integration for multi-provider routing
- RAG evaluation examples
- agent workflow tracing
- OpenTelemetry traces
- budget guardrails
- CI gates for evaluation regression checks

## Report Contract

JSON reports declare a schema version and content mode:

- `schema_version`: currently `pangolin-eval.report.v3`
- `content_mode`: `full` or `metadata_only`

See [docs/REPORT_SCHEMA.md](docs/REPORT_SCHEMA.md), [schemas/report.v3.json](schemas/report.v3.json), and [schemas/pricing-catalog.v1.json](schemas/pricing-catalog.v1.json).

## Open-Core Direction

This repo is the public CLI/library foundation. Commercial extensions may build on top of this engine for UI, run history, team workflows, recommendations, alerts, and executive reports.

The open-source project should remain useful on its own: local reports, transparent metrics, reproducible examples, and CI-friendly gates stay public.

## Configuration

See [examples/simple_model_compare/config.json](examples/simple_model_compare/config.json).

Model entries include:

- `id`: display name used in reports
- `provider`: `mock` or `openai_compatible`
- `api_model`: provider model id, if different from `id`
- `input_price_per_1m`: input token cost estimate
- `output_price_per_1m`: output token cost estimate

Prompt entries include:

- `id`: prompt case identifier
- `messages`: chat-style messages
- `expected_keywords`: optional simple quality check

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
