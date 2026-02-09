---
name: update-dotfiles
description: "Safely update this wrapper dotfiles repo and the common submodule: detect active profile (work/home), collect unstaged changes, route edits to the correct layer, and update/push submodule pointers without disturbing unrelated local edits."
---

# Update Dotfiles

## Overview
Use this skill when changing dotfiles in the wrapper repo that contains a `common/` submodule plus environment overlays (`work/` and optionally `home/`).

Goals:
- Keep environment-specific changes in the correct overlay (`work/` or `home/`).
- Keep shared changes in `common/`.
- Preserve unrelated unstaged work.
- Push `common` first, then update the wrapper submodule pointer.

## Quick Start

1) Snapshot current state:
```bash
bash common/codex/skills/update-dotfiles/scripts/dotfiles_snapshot.sh
```

2) Route edits using `references/routing.md`.

3) Commit/push in order:
```bash
# shared edits in common
git -C common add <paths>
git -C common commit -m "<message>"
git -C common push origin main

# then pointer update in wrapper
git add common
git commit -m "Update common submodule"
```
If pushes are flaky from a work environment, follow `references/push-from-work.md`.

## Workflow

1) Locate roots
- Wrapper repo root: `git rev-parse --show-toplevel`
- Common submodule root: `<wrapper>/common`

2) Detect profile (`work` or `home`)
- Prefer explicit `DOTFILES_PROFILE` if set.
- If only one overlay exists, use it.
- If both exist, inspect `~/.zshrc.work` and `~/.zshrc.home` symlink targets.
- If still ambiguous, ask the user before writing overlay files.

3) Collect staged/unstaged context
- Run the snapshot script above.
- Always check both repos:
  - `git status --short`
  - `git -C common status --short`

4) Route edits to correct layer
- OpenAI/work-machine-specific settings belong in `work/`.
- Home-machine-specific settings belong in `home/`.
- Shared defaults, shared skills, and shared tooling belong in `common/`.
- Wrapper glue (`install.sh`, `bin/create-agent`, wrapper `AGENTS.md`) belongs in wrapper root repo.

5) Edit with minimal scope
- Stage only intended paths.
- Do not use stash/autostash/reset to get clean commits.
- If unrelated edits are present, commit targeted files only.

6) Commit and push safely
- Commit `common` first and push to `origin/main`.
- Then commit wrapper submodule pointer update (`common` entry) separately.
- If wrapper has unrelated modified files, keep them unstaged unless requested.
- If pushes fail/hang in work environments, use the fallback sequences in `references/push-from-work.md`.

## Notes
- Shared skills should live under `common/codex/skills/<skill-name>`.
- To edit a shared skill via `~/.codex/skills`, symlink:
  - `~/.codex/skills/<skill-name> -> <wrapper>/common/codex/skills/<skill-name>`
- This makes local edits appear as normal unstaged git changes in `common`.

## Resources

- `scripts/dotfiles_snapshot.sh`: one-command status snapshot across wrapper + common plus profile guess.
- `references/routing.md`: path routing rules (`work` vs `home` vs `common` vs wrapper).
- `references/push-from-work.md`: repeatable push/rebase/auth fallback flow for common and wrapper repos.
