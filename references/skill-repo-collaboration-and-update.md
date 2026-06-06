# Skill repo collaboration and update hygiene

Use this reference when the task is to update, sync, or inspect the `video-to-article` skill repository itself, especially when multiple GitHub repos/forks exist.

## Canonical repo rule

- Treat the shared upstream repo as the canonical source of truth.
- Keep fork remotes available only for recovery, PR comparison, or pulling changes that have not yet landed upstream.
- Do not assume the repo named `origin` is correct until you inspect remotes and branch tracking.

Recommended inspection sequence:

```bash
cd /Users/circleghost/Desktop/開發/SKILL/video-to-article
git remote -v
git branch -vv
git status --short --branch
git fetch origin main
git log --oneline --decorate --graph -6 --all
```

Then identify:

- which remote is canonical upstream
- which remote is the fork
- which branch the local `main` tracks
- whether local is ahead/behind canonical upstream
- whether a fork-only commit has already been merged upstream via PR

## Safe update flow

1. Fetch canonical upstream first.
2. If a fork has potentially newer work, fetch the fork and compare heads.
3. Prefer PR merge into canonical upstream for fork-originated work.
4. After the PR lands upstream, rebase local work onto canonical upstream to remove unnecessary merge noise.
5. Verify script syntax if Python scripts changed.
6. Before pushing, run a dry-run push to the intended remote.

Example:

```bash
git fetch origin main
git fetch fork main
git rev-list --left-right --count origin/main...HEAD
git rev-list --left-right --count fork/main...HEAD
git rebase origin/main
python3 -m py_compile scripts/*.py
git push --dry-run origin main
```

## Permission and identity pitfall

Git config `user.name` / `user.email` only affects commit authorship. It does not prove which GitHub account the credential helper will use for push.

Always test the actual push identity with:

```bash
git push --dry-run origin main
```

If dry-run push to canonical upstream returns `403` but fork push works, the machine is authenticated as an account that can write to the fork but not to upstream. Fix by either:

- adding that authenticated account as collaborator on the canonical repo, or
- switching the machine's Git credential to an account that has upstream write access.

Do not push new work to the fork merely because upstream push is denied, unless the user explicitly chooses a fork + PR workflow. Otherwise the repo will split again.

## User-facing explanation pattern

When reporting the state, explicitly separate three things:

1. **Runtime skill directory** — the local path Hermes is actually loading.
2. **Canonical update source** — the remote that normal pulls should follow.
3. **Push target and credential reality** — which remote dry-run push can actually write to.

Avoid saying “updated the repo” until you specify whether the update is local-only, pushed to upstream, or pushed to a fork.