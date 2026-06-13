# Extension Points

PangolinEval is designed around local files and small Python APIs. Downstream tools can integrate without depending on a hosted service.

## Provider Adapters

Provider adapters implement `Provider.complete(model, prompt)` and return a `Completion`.

Existing providers:

- `mock`: deterministic examples and tests
- `openai_compatible`: OpenAI-compatible `/chat/completions` APIs

## Report Artifacts

Stable artifacts are written as JSON:

- `report.json`: model/prompt comparison report
- `rag_report.json`: RAG evaluation report
- `tracecards.json`: agent/workflow TraceCards
- `pricing_catalog.json`: optional pricing source metadata

Schemas live in `schemas/`.

## Import And Export

`pangolin-eval export-otel` converts supported artifacts into OTel-style spans:

```bash
pangolin-eval export-otel \
  --input reports/simple_model_compare/report.json \
  --out reports/simple_model_compare/otel.json
```

Supported inputs:

- `pangolin-eval.report.*`
- `pangolin-eval.tracecards.v1`

## Gateway Examples

OpenAI-compatible and LiteLLM gateway templates live in:

- `examples/openai_compatible/config.json`
- `examples/litellm_gateway/config.json`

Both examples use environment variables for API keys and contain no secrets.
