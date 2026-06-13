# Report Schema

PangolinEval writes a versioned JSON report at `report.json`.

Current schema:

```text
schemas/report.v3.json
schema_version: pangolin-eval.report.v3
```

`schemas/report.v1.json` and `schemas/report.v2.json` are kept for older reports.

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
- Prompt results can include attribution fields: `feature`, `workflow`, `environment`, `prompt_version`, and `customer_user_hash`.
- Pricing provenance fields include `pricing_source`, `pricing_source_url`, and `pricing_updated_at`.
- `aggregations` summarizes cost, quality, latency, and reliability by model, prompt, feature, workflow, environment, prompt version, and model group.
- Provider `metadata` is intentionally extensible because usage fields vary across APIs.

## Pricing Catalog

Optional pricing catalogs use:

```text
schemas/pricing-catalog.v1.json
schema_version: pangolin-eval.pricing.v1
```

Set `pricing_catalog` in a config file to load catalog prices and provenance. Add `price_override: true` on a model entry to keep model-level prices instead of applying the catalog.

## RAG Report

RAG evaluations write `rag_report.json` and use:

```text
schemas/rag-report.v1.json
schema_version: pangolin-eval.rag_report.v1
```

RAG results include retrieved context tokens, answer tokens, answer coverage, simple faithfulness, context efficiency, unused-context signal, missing-citation flag, latency, and estimated cost.

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

TraceCards summarize per-task cost, latency, tokens, retries, failures, cache hits, repeated steps, and cost per successful task.
