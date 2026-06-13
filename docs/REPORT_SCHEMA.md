# Report Schema

PangolinEval writes a versioned JSON report at `report.json`.

Current schema:

```text
schemas/report.v1.json
schema_version: pangolin-eval.report.v1
```

## Content Modes

Reports support two content modes:

- `full`: saves model response text in `results[].response`.
- `metadata_only`: saves `null` in `results[].response` and adds `response_content_omitted: true` to result metadata.

Quality scoring still uses the model response during the run. In `metadata_only` mode, the response is omitted only from the saved artifacts.

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
- Token counts, latency, estimated cost, quality score, and provider metadata remain available in both modes.
- Prompt messages are not written to reports in the current schema.
- Provider `metadata` is intentionally extensible because usage fields vary across APIs.

Future schema versions will add reliability, attribution, pricing provenance, budget gates, RAG metrics, and agent TraceCards.
