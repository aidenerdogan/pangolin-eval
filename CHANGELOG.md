# Changelog

All notable public changes are documented here.

## v0.2.0 - 2026-06-15

Post-release polish focused on public contract readiness.

### Added

- Public compatibility policy for CLI, config, report, RAG, TraceCard, pricing, and export contracts.
- Migration notes for moving from `v0.1.0` to `v0.2.0`.
- CI-gate example config demonstrating budget, latency, quality, and reliability thresholds.
- Version-consistency regression coverage for package metadata.
- `v0.2.0` release notes.

### Changed

- Package version updated to `0.2.0`.
- CI validates the CI-gate example.

## v0.1.0 - 2026-06-14

Initial public release of `pangolin-eval`.

### Added

- Local CLI and Python package for comparing LLM workloads across cost, latency, quality, and reliability.
- Mock provider for no-key demos and an OpenAI-compatible `/chat/completions` provider adapter.
- Config-driven prompt/model comparisons with retry-aware, failure-tolerant reports.
- Markdown, JSON, and optional static HTML reports.
- Metadata-only content mode for privacy-conscious saved artifacts.
- Budget, latency, quality, and reliability gates with CI-friendly exit codes.
- Attribution and pricing provenance summaries.
- Weighted quality evaluators: `keyword`, `contains`, `regex`, and `exact`.
- Configurable token estimation fallbacks: `char_4`, `whitespace`, and `openai_chat`.
- Synthetic RAG evaluation CLI with context efficiency, citation, repeated-context, and oversized-context diagnostics.
- Agent/workflow TraceCards with retry, failure, cache, repeated-step, wasted-cost, and loop-risk diagnostics.
- Rule-based recommendations-lite and OTel-style export for reports and TraceCards.
- Public JSON schemas for comparison reports, RAG reports, trace events, TraceCards, pricing catalogs, eval configs, and OTel exports.
- OpenAI-compatible, LiteLLM, Ollama, and vLLM example configs.
- Docker Compose no-key demos.

### Security And Safety

- Redacted provider HTTP error bodies.
- Added OpenAI-compatible provider safety checks for HTTPS, loopback URLs, API key environment names, and known host/key pairings.
- Constrained regex evaluator patterns to reduce ReDoS risk.
- Escaped Markdown fences in saved reports.
- Pinned GitHub Actions to commit SHAs and set minimal workflow permissions.
