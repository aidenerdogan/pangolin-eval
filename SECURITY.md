# Security Policy

## Supported Versions

`pangolin-eval` is pre-1.0 software. Security and privacy fixes are handled on the latest released version.

| Version | Supported |
| --- | --- |
| `v0.2.x` | Yes |
| older versions | No |

## Reporting A Vulnerability

Do not open a public issue with sensitive details.

Use GitHub private vulnerability reporting from the repository Security tab. If that path is unavailable, open a minimal public issue saying you have a security or privacy concern and avoid including secrets, private prompts, customer data, logs, retrieved documents, or full responses.

Useful non-sensitive context:

- affected `pangolin-eval` version
- affected command or file type
- whether `full` or `metadata_only` content mode was used
- high-level impact, without private data

## Sensitive Data Reminder

`metadata_only` mode omits model response text from saved reports. Use it for real evaluations unless prompts and responses are safe to store and share.
