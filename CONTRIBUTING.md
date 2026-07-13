# Contributing

## Branching

We use an environment-branch model — see
[`docs/branching-strategy.md`](docs/branching-strategy.md) for the full flow.

TL;DR: branch off `dev`, PR back into `dev`, promote `dev → staging → main`.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Before opening a PR

Run the same checks CI runs:

```bash
ruff check . && ruff format --check .
mypy
pytest
```

## Commit / PR conventions

- One logical change per PR; keep them small and reviewable.
- Never commit secrets or environment-specific values (see `.env.example`).
- Don't change behavior and structure in the same commit.
