# Release Process

This document describes the public release path for `pangolin-eval`.

## Versioning

The latest public release target is `v0.2.0`.

Keep these version values in sync before tagging:

- `pyproject.toml`
- `setup.py`
- `src/pangolin_eval/__init__.py`
- `CHANGELOG.md`
- `docs/releases/vX.Y.Z.md`

## Pre-Release Checks

Run from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
find schemas examples -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
PYTHONPATH=src python3 -m pangolin_eval.cli validate --config examples/simple_model_compare/config.json
PYTHONPATH=src python3 -m pangolin_eval.cli validate --config examples/ci_gate/config.json
PYTHONPATH=src python3 -m pangolin_eval.cli validate --config examples/openai_compatible/config.json
PYTHONPATH=src python3 -m pangolin_eval.cli validate --config examples/litellm_gateway/config.json
PYTHONPATH=src python3 -m pangolin_eval.cli validate --config examples/ollama_openai_compatible/config.json
PYTHONPATH=src python3 -m pangolin_eval.cli validate --config examples/vllm_openai_compatible/config.json
PYTHONPATH=src python3 -m pangolin_eval.cli run --config examples/simple_model_compare/config.json --out reports/simple_model_compare --content-mode metadata-only --html
PYTHONPATH=src python3 -m pangolin_eval.cli run --config examples/ci_gate/config.json --out reports/ci_gate --content-mode metadata-only --html
PYTHONPATH=src python3 -m pangolin_eval.cli rag --config examples/rag_eval/config.json --out reports/rag_eval --content-mode metadata-only --html
PYTHONPATH=src python3 -m pangolin_eval.cli trace --input examples/agent_trace/trace_events.json --out reports/agent_trace --html
PYTHONPATH=src python3 -m pangolin_eval.cli export-otel --input reports/simple_model_compare/report.json --out reports/simple_model_compare/otel.json
python3 -m venv /tmp/pangolin-eval-release-venv
/tmp/pangolin-eval-release-venv/bin/python -m pip install --upgrade pip build
/tmp/pangolin-eval-release-venv/bin/python -m build
/tmp/pangolin-eval-release-venv/bin/python -m pip install --force-reinstall dist/pangolin_eval-*.whl
/tmp/pangolin-eval-release-venv/bin/pangolin-eval --help
```

Before tagging, confirm:

- `git status --short --ignored` shows only expected ignored generated files.
- No generated `reports/` artifacts are staged.
- No `.env`, credentials, private notes, customer data, or Pro implementation files are staged.
- GitHub Actions pass on `main`.

## Tag And GitHub Release

Create and push an annotated tag:

```bash
git tag -a v0.2.0 -m "pangolin-eval v0.2.0"
git push origin v0.2.0
```

The tag-driven release workflow builds source and wheel distributions, verifies the
installed CLI, and creates a GitHub Release with the artifacts attached.

If a release must be recreated, delete the GitHub Release and tag first, then push a
new annotated tag.
