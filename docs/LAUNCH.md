# Launch Notes

`pangolin-eval` helps AI teams answer a practical production question:

> Which model gives enough quality for this task at an acceptable cost, latency, and reliability?

## Short Description

Open-source, local-first toolkit for comparing LLM, RAG, and agent workloads across cost, latency, quality, and reliability.

## Suggested Demo Flow

1. Run the no-key mock comparison:

```bash
PYTHONPATH=src python -m pangolin_eval.cli run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare \
  --html
```

2. Inspect the Markdown report:

```bash
cat reports/simple_model_compare/report.md
```

3. Show the privacy posture with metadata-only output:

```bash
PYTHONPATH=src python -m pangolin_eval.cli run \
  --config examples/simple_model_compare/config.json \
  --out reports/simple_model_compare_private \
  --content-mode metadata-only
```

4. Show CI-friendly validation and gates:

```bash
PYTHONPATH=src python -m pangolin_eval.cli validate \
  --config examples/ci_gate/config.json
PYTHONPATH=src python -m pangolin_eval.cli run \
  --config examples/ci_gate/config.json \
  --out reports/ci_gate \
  --content-mode metadata-only
```

## Launch Post Draft

I released `pangolin-eval`, an open-source CLI for evaluating LLM workloads across cost, latency, quality, and reliability.

The core idea is simple: model quality is not enough by itself. Production teams also need to know whether a model is cheap enough, fast enough, reliable enough, and safe enough to use for a specific workflow.

The first public release includes no-key demos, OpenAI-compatible provider support, budget and quality gates, metadata-only reports, RAG diagnostics, agent TraceCards, pricing provenance, recommendations-lite, and versioned JSON schemas.

The project is local-first and dependency-light so teams can inspect the methodology, run it in CI, and keep sensitive prompt/response content out of saved artifacts when needed.

Repo: https://github.com/aidenerdogan/pangolin-eval

## First Feedback To Ask For

- Is the quickstart clear enough to run in under 10 minutes?
- Which provider or gateway examples would help most?
- Are the report fields useful for a real model-selection decision?
- What would make the CI gate easier to adopt?
- Which team workflow would be most useful next: history, dashboard, recommendations, alerts, or executive summaries?
