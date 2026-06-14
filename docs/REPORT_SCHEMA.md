# Report Schema

PangolinEval writes a versioned JSON report at `report.json`.

Evaluation configs are documented by:

```text
schemas/eval-config.v1.json
```

Current schema:

```text
schemas/report.v4.json
schema_version: pangolin-eval.report.v4
```

Older report schemas are kept for compatibility.

## Content Modes

Reports support two content modes:

- `full`: saves model response text in `results[].response`.
- `metadata_only`: saves `null` in `results[].response` and adds `response_content_omitted: true` to result metadata for successful provider calls.

Quality scoring still uses the model response during the run. In `metadata_only` mode, the response is omitted only from the saved artifacts. Failed provider calls also use `response: null` and include `success: false`, `status`, and `error` fields.

Use metadata-only mode for sensitive evaluation sets:

```bash
pangolin-eval run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare_private \
  --content-mode metadata-only
```

## Contract Notes

- `schema_version` identifies the report format.
- `content_mode` identifies whether response content is present.
- Token counts, latency, estimated cost, quality score, reliability fields, gate results, and provider metadata remain available in both modes.
- Prompt messages are not written to reports in the current schema.
- `usage_source` distinguishes provider-reported usage from estimated usage.
- `token_counter` can be set per model for estimated usage fallback when provider usage is unavailable.
- Quality scoring can combine `expected_keywords` with weighted `keyword`, `contains`, `regex`, and `exact` evaluators.
- Regex evaluators are bounded: patterns must be at most 256 characters and nested quantifiers are rejected.
- Prompt results can include attribution fields: `feature`, `workflow`, `environment`, `prompt_version`, and `customer_user_hash`.
- Pricing provenance fields include `pricing_source`, `pricing_source_url`, and `pricing_updated_at`.
- `aggregations` summarizes cost, quality, latency, and reliability by model, prompt, feature, workflow, environment, prompt version, and model group.
- `recommendations` contains auditable rule-based suggestions for model switches, context trimming, max-token caps, caching, and fallback review.
- Provider `metadata` is intentionally extensible because usage fields vary across APIs.

## Pricing Catalog

Optional pricing catalogs use:

```text
schemas/pricing-catalog.v1.json
schema_version: pangolin-eval.pricing.v1
```

Set `pricing_catalog` in a config file to load catalog prices and provenance. Add `price_override: true` on a model entry to keep model-level prices instead of applying the catalog.

OpenAI-compatible configs restrict credential forwarding by default. Use HTTPS
provider URLs unless targeting loopback, and use a known safe API key/host
pairing or the `PANGOLIN_EVAL_` prefix. Set `allow_unsafe_api_key_env: true`
only for trusted local configs that need a custom environment variable name or
non-default host.

## RAG Report

RAG evaluations write `rag_report.json` and use:

```text
schemas/rag-report.v1.json
schema_version: pangolin-eval.rag_report.v1
```

RAG results include retrieved context tokens, answer tokens, answer coverage, simple faithfulness, context efficiency, unused-context signal, repeated-context signal, oversized-context flag, missing-citation flag, latency, estimated cost, and cost per covered answer.

## TraceCards

TraceCard input events use:

```text
schemas/trace-events.v1.json
schema_version: pangolin-eval.trace_events.v1
```

Generated TraceCards use:

```text
schemas/tracecards.v1.json
schema_version: pangolin-eval.tracecards.v1
```

TraceCards summarize per-task cost, latency, tokens, retries, failures, failed tool calls, cache hits, repeated steps, wasted cost, loop risk, and cost per successful task.

## Static HTML Reports

The `run`, `rag`, and `trace` commands accept `--html` to write dependency-free HTML
summaries next to the JSON and Markdown artifacts.

## OTel-Style Export

`pangolin-eval export-otel` writes:

```text
schemas/otel-export.v1.json
schema_version: pangolin-eval.otel_export.v1
```

Supported inputs are standard comparison reports and TraceCards.
