# Compatibility Policy

`pangolin-eval` is pre-1.0 software. The project aims to keep normal workflows
stable, but public contracts can still change while the CLI and schemas settle.

## Public Contracts

The following surfaces are treated as public:

- CLI commands and flags documented in `pangolin-eval --help`
- evaluation config files documented by `schemas/eval-config.v1.json`
- comparison reports with `schema_version: pangolin-eval.report.*`
- RAG reports with `schema_version: pangolin-eval.rag_report.*`
- trace event inputs with `schema_version: pangolin-eval.trace_events.*`
- TraceCards with `schema_version: pangolin-eval.tracecards.*`
- pricing catalogs with `schema_version: pangolin-eval.pricing.*`
- OTel-style exports with `schema_version: pangolin-eval.otel_export.*`

## Pre-1.0 Rules

- Patch releases should avoid breaking CLI flags or JSON fields.
- Minor releases may add fields, commands, examples, and schema versions.
- Breaking changes should be documented in `CHANGELOG.md` and `docs/MIGRATIONS.md`.
- Existing schema files stay in `schemas/` when a new schema version is introduced.
- Report consumers should branch on `schema_version`, not package version.

## 1.0 Stability Bar

`v1.0.0` should mean:

- documented CLI/config/report contracts are stable;
- migration guidance exists for supported schema versions;
- at least one post-`v0.1.0` public release cycle has tested packaging and user-facing docs;
- downstream consumers can use the public package boundary instead of duplicating engine logic.

Until then, pin exact versions for automation:

```bash
python -m pip install \
  https://github.com/aidenerdogan/pangolin-eval/releases/download/v0.2.3/pangolin_eval-0.2.3-py3-none-any.whl
```
