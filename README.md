# onboard-agent

Onboarding agent.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

## Branching & environments

Three long-lived branches, each mapped to a deployment environment:

```
feature/*  ──►  dev  ──►  staging  ──►  main
                 │          │            │
             development  staging     production
```

- **How to work:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Full flow & rules:** [`docs/branching-strategy.md`](docs/branching-strategy.md)
- **One-time GitHub config (environments, branch protection):** [`docs/github-setup.md`](docs/github-setup.md)
