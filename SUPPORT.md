# Support

`pangolin-eval` is an early open-source project. The best support path is to open a GitHub issue with enough context to reproduce or understand the request.

## Good Issue Types

- Bug reports for CLI crashes, invalid reports, schema mismatches, or provider adapter problems.
- Documentation gaps where the quickstart, examples, or release notes are unclear.
- Integration requests for providers, gateways, CI systems, or report consumers.
- Feedback from trying the no-key demos, RAG evaluation, TraceCards, or CI gates.

## Before Opening An Issue

Please include:

- `pangolin-eval` version, from `pangolin-eval --version` or package metadata.
- Python version and operating system.
- The command you ran.
- The config shape or a redacted/minimal reproduction.
- Whether the report used `full` or `metadata_only` content mode.

Do not paste API keys, private prompts, customer data, retrieved documents, logs from confidential systems, or full response text unless it is synthetic and safe to share publicly.

## Security Or Privacy

If you suspect a credential leak, unsafe provider behavior, report redaction problem, or another security/privacy issue, do not open a public issue with sensitive details. Open a minimal public issue saying there is a security concern and avoid sharing secrets or customer data.

## Commercial Help

The open-source CLI is useful on its own. Commercial services and Pro workflows may build on it for team history, dashboards, recommendation queues, alerts, and executive reports, but core measurement behavior should stay visible in this public engine.
