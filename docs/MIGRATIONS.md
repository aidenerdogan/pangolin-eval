# Migration Notes

Use this file when moving between public `pangolin-eval` releases.

## v0.1.0 to v0.2.0

No breaking changes are expected.

### What Changed

- Package version is now `0.2.0`.
- Added a public compatibility policy.
- Added migration notes for future schema and CLI changes.
- Added a CI-gate example config that demonstrates budget, latency, quality, and reliability thresholds.
- Added regression coverage to keep package version declarations aligned.

### Recommended Action

- Existing `v0.1.0` configs and reports should continue to work.
- If you automate around generated JSON, continue branching on `schema_version`.
- If you install from GitHub Releases, update local wheel references from `0.1.0` to the latest `v0.2.x` release.

## v0.2.0 to v0.2.2

No breaking changes are expected.

### What Changed

- `v0.2.1` updated pinned GitHub Actions to Node 24-compatible versions.
- `v0.2.2` added support docs, launch notes, issue templates, and `pangolin-eval --version`.

### Recommended Action

- Keep using `schema_version` for report consumers.
- Use `--content-mode metadata-only` for real evaluations unless prompts and responses are safe to store.
