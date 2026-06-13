# Extension Points

PangolinEval is designed around local files and small Python APIs. Downstream tools can integrate without depending on a hosted service.

## Provider Adapters

Provider adapters implement `Provider.complete(model, prompt)` and return a `Completion`.

Existing providers:

- `mock`: deterministic examples and tests
- `openai_compatible`: OpenAI-compatible `/chat/completions` APIs

Provider configs can set `token_counter` to choose the fallback estimator used when a
provider response does not include usage. Supported counters are `char_4`, `whitespace`,
and `openai_chat`.

## Evaluators

Prompt configs can combine legacy `expected_keywords` with weighted `evaluators`.
Built-in evaluator types are:

- `keyword`: case-insensitive substring check
- `contains`: explicit substring check
- `regex`: Python regular expression check
- `exact`: whole-response exact match after trimming whitespace

Evaluator entries support optional `weight` and `case_sensitive` fields.

## Report Artifacts

Stable artifacts are written as JSON:

- `report.json`: model/prompt comparison report
- `rag_report.json`: RAG evaluation report
- `tracecards.json`: agent/workflow TraceCards
- `pricing_catalog.json`: optional pricing source metadata

Schemas live in `schemas/`.

Commands can also write static HTML artifacts with `--html`:

- `report.html`
- `rag_report.html`
- `tracecards.html`

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
- `examples/ollama_openai_compatible/config.json`
- `examples/vllm_openai_compatible/config.json`

These examples use environment variables for API keys and contain no secrets.
