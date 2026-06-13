# Report Schema

PangolinEval writes a versioned JSON report at `report.json`.

Current schema:

```text
schemas/report.v2.json
schema_version: pangolin-eval.report.v2
```

`schemas/report.v1.json` is kept for older reports.

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
- Provider `metadata` is intentionally extensible because usage fields vary across APIs.

Future schema versions will add attribution, pricing provenance, RAG metrics, and agent TraceCards.
