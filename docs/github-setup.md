# GitHub Setup Guide

One-time configuration to make the branching strategy enforceable. Do this in
the GitHub web UI (repo **Settings**). Requires admin on the repo.

All paths below are relative to:
`https://github.com/yahia-abourgailah/onboard-agent/settings`

---

## 1. Environments

**Settings → Environments → New environment.** Create three, named exactly:

| Environment   | Deployment branch rule | Protection                                   |
|---------------|------------------------|----------------------------------------------|
| `development` | `dev`                  | None (fast feedback).                         |
| `staging`     | `staging`              | Optional: 1 required reviewer.                |
| `production`  | `main`                 | **Required reviewers** (you); wait timer opt. |

For each environment:

1. Under **Deployment branches and tags**, choose **Selected branches** and add
   the matching branch (`dev` / `staging` / `main`). This stops the wrong branch
   from ever deploying to it.
2. For `production` (and optionally `staging`): tick **Required reviewers** and
   add yourself. Deploys will pause for approval.
3. Add environment secrets/vars under **Environment secrets** /
   **Environment variables** (e.g. `DEPLOY_TOKEN`, API endpoints). These are
   injected only into jobs targeting that environment by `deploy.yml`.

> The workflow already selects the environment per branch — you only need to
> create the environments and attach their protection + secrets.

---

## 2. Branch protection

**Settings → Branches → Add branch ruleset** (or classic *Branch protection
rules*). Create one rule per branch. Suggested settings:

| Setting                                   | `main` | `staging` | `dev` |
|-------------------------------------------|:------:|:---------:|:-----:|
| Require a pull request before merging     |   ✅   |    ✅     |  ✅   |
| Require approvals (count)                  |   1    |    1      |  0    |
| Require status checks to pass             |   ✅   |    ✅     |  ✅   |
| → required checks: `Lint (ruff)`, `Type check (mypy)`, `Tests (pytest)` | ✅ | ✅ | ✅ |
| Require branches to be up to date         |   ✅   |    ✅     |  —    |
| Require conversation resolution           |   ✅   |    ✅     |  —    |
| Require linear history                    |   ✅   |    ✅     |  —    |
| Do not allow bypassing the above          |   ✅   |    —      |  —    |
| Block force pushes                        |   ✅   |    ✅     |  ✅   |

> The status check names must match the job `name:` values in `ci.yml`. They
> only appear in the picker after CI has run at least once — merge this scaffold
> first, then add the checks.

---

## 3. Default branch & merge settings

- **Settings → General → Default branch:** keep `main`.
- **Pull Requests:** enable **Allow squash merging**, disable merge commits and
  rebase merging (keeps history linear and matches the "require linear history"
  rule above). Enable **Automatically delete head branches**.

---

## 4. Optional: configure via CLI later

If you install the GitHub CLI, most of the above can be scripted:

```bash
gh auth login
# Environment with a required reviewer (production):
gh api -X PUT repos/yahia-abourgailah/onboard-agent/environments/production \
  -f "reviewers[][type]=User" -F "reviewers[][id]=$(gh api user -q .id)"
# Branch protection (main) — see: gh api repos/:owner/:repo/branches/main/protection
```

Tell me when you're ready and I can generate the full `gh`/API script.
