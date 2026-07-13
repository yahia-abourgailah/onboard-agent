# Branching Strategy

An environment-branch model: three long-lived branches, each mapped to one
deployment environment. Code always flows in one direction.

```
feature/*  ──►  dev  ──►  staging  ──►  main
                 │          │            │
             development  staging     production
```

## Branches

| Branch    | Environment   | Purpose                                   | Deploys                       |
|-----------|---------------|-------------------------------------------|-------------------------------|
| `main`    | `production`  | Production-ready, released code.          | On merge (protected + review) |
| `staging` | `staging`     | Pre-production validation / UAT.          | On merge                      |
| `dev`     | `development` | Integration of completed features.        | On merge                      |
| `feature/*` | —           | One branch per unit of work.              | Never (CI only)               |

## Flow

1. **Start work** off the latest `dev`:
   ```bash
   git switch dev && git pull
   git switch -c feature/short-description
   ```
2. **Open a PR into `dev`.** CI (lint, type check, tests) must pass. Merge.
   → auto-deploys to **development**.
3. **Promote to staging:** open a PR `dev → staging`. Merge.
   → auto-deploys to **staging**. Validate / UAT here.
4. **Release:** open a PR `staging → main`. Requires review. Merge.
   → deploys to **production**.

## Rules

- Never commit directly to `dev`, `staging`, or `main` — always via PR.
- Only ever **promote forward** (`dev → staging → main`). Never merge `main`
  back down; if a hotfix lands on `main`, cherry-pick or forward-merge it into
  `staging` and `dev` to keep them in sync.
- Keep branches short-lived. Rebase or merge `dev` into your feature branch to
  stay current.
- Environment-specific config lives in each GitHub Environment's secrets/vars,
  never in the repo. See [`github-setup.md`](./github-setup.md).

## Hotfixes

Urgent production fix:
```bash
git switch main && git pull
git switch -c hotfix/short-description
# fix, PR into main, review, merge -> production
```
Then forward-port the fix into `staging` and `dev` so they don't regress.
