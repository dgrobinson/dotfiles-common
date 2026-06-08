# Codex Agent Instructions

This file is my global guidance for Codex (applies across repos).
Do not add secrets here.
## Repo guardrails

- Do not disrupt unstaged changes in this dotfiles repo (avoid autostash, reset, or checkout that alters the working tree).
- When pushing isolated changes while other edits are present, use a clean worktree or cherry-pick into a fresh branch.
- Run `./setup-hooks.sh` to install no-stash guardrails for this repo (blocks `git stash` and `--autostash`).
- At session start in a git repo, fetch and compare the current checkout to the repo's upstream default branch before substantive work.
- If a local default-branch checkout has uncommitted changes and is behind or diverged from upstream, do not continue in place. Move the work to a fresh worktree from current upstream instead.

## Engineering guidance

- Prefer the simplest change that makes the code easier to understand next time.
- Before adding a new abstraction, ask whether it reduces cognitive complexity across the repo, not just whether it makes the current patch look cleaner.
- Do not add trivial helpers, wrapper types, fallback layers, or mini-frameworks for simple logic.
- When existing AI-generated code looks strange and there is no real historical reason for it, it is acceptable to simplify or delete it instead of preserving it as legacy design.

## Practice What We Preach

Guidance is training data. When a note is meant to shape future agents, write it in the voice you want copied: bottom line first, useful distinction early, caveat beside claim, evidence inline.

Put judgment before evidence. Raw notes can preserve the source trail; agent-facing docs should give the clean mental model first, then point into the raw pack when the reader needs to check it.

Keep instruction layers clean: cross-repo Codex defaults here, repo rules in the nearest `AGENTS.md`, vault writing rules in `~/vault/AGENTS.md` and `~/vault/agent-guidance/`.

## Repo layout: template clone + git worktrees (preferred)

ELI5: A `git worktree` is an extra working folder that shares the same underlying git history as a base clone.
This is faster and lighter than re-cloning a repo for every task/branch.

Conventions:
- Keep one "template" clone per repo that you do not edit day-to-day.
  - In practice, organize worktrees under a single working directory like:
    - `<working-dir>/template/` (full clone, stays on `main`)
    - `<working-dir>/<agent-or-task>/` (one worktree per agent/task)
- Create one worktree per agent/task as a sibling directory next to `template/`.
  - Worktrees share git objects (fast), but they do NOT share dependency installs (you still run `npm ci`, `pip install`, etc per worktree).

Preferred workflow: `create-agent`

When you're standing in `<working-dir>` (the parent of `template/`), use:
- `create-agent foo`

`create-agent` will:
- `git fetch` + fast-forward `template/` to the latest `main`
- create a sibling worktree at `<working-dir>/foo` (default branch: `agent/foo`)

Equivalent git commands (run from `template/`):
- Refresh remote refs: `git fetch origin`
- Update template main: `git checkout main && git pull --ff-only origin main`
- New worktree on a new branch: `git worktree add -b agent/foo ../foo origin/main`
- Worktree for an existing branch: `git worktree add ../foo agent/foo`
- List worktrees: `git worktree list`
- Remove a worktree directory when done:
  - `git worktree remove ../foo`
  - (Optional) `git worktree prune`

## Batch worktrees (multiple parallel agents)

- If `CODEX_WORKTREE` is set, treat it as the project root for all file ops.
- Use `CODEX_WORKTREE_NAME` to label outputs or logs when multiple agents run.

`codexplex` is a helper for batch runs:
- It can create worktrees under a batch directory and print per-worktree commands for manual launch.
- It sets `CODEX_PROJECT_ROOT` to the batch dir (useful when the batch dir is a sandbox root).

Note:
- `codexplex --repo ...` will create a fresh clone inside `<batch-dir>/.source` for that batch.
  - This is convenient and self-contained, but it is slower than using a persistent template clone.
- Preferred approach: create worktrees from your template clone (sharing git objects), then run `codexplex <batch-dir>` to print the per-worktree launch commands.

`codex-batch-panes` is a deprecated alias for `codexplex`.

If you need the git root, prefer:
- `git -C "$CODEX_WORKTREE" rev-parse --show-toplevel`

## Batch work structure

- Batch tasks should be parallelizable; avoid sequencing dependencies between briefs in the same batch.
- Name batches as a themed series (e.g., trees: arbor, birch, cypress; nautical: anchor, bowline, compass).
- Track each batch under `docs/batches/<batch-name>` at the repo root while work is active.
- When a batch is complete, move its record to `docs/archived/<batch-name>`.

## PR reference style

- When referencing a GitHub pull request, include both the PR number and a human-friendly ref name (usually the branch name and/or worktree/window name), so readers do not have to memorize which PR is which.
  - Example: `PR #423 (agent/birch-parity-guardrails)` rather than `PR #423`.

## Remote Codex box on DigitalOcean

- The current remote Codex Droplet is `codex-box` at `68.183.141.62`.
  - Local SSH shortcut: `ssh codex-box`
  - DigitalOcean ID: `575783325`
  - Region/size: `nyc1`, `s-2vcpu-4gb` (about $24/month while it exists)
  - OS: Ubuntu 24.04
- The original `codex-box` Droplet (`571314844`, `157.245.81.87`) became unreachable after an OS-level firewall rule was locked to an old client IP; it was replaced and destroyed on June 6, 2026.
- Do not add a second per-IP `ufw` lock inside Ubuntu. Use the DigitalOcean cloud firewall `codex-box-ssh-only` as the source-IP control point.
- The box has Node.js 20, Git, GitHub CLI, Codex CLI, Python, build tools, ripgrep, tmux, and zsh installed.
- The box has the dotfiles wrapper cloned at `/home/codex/code/dgr-dotfiles`; helper scripts are available as `create-agent`, `codexplex`, `codex-batch-panes`, and `codex-workshop`.
- GitHub operations on the box use `gh` HTTPS credentials plus URL rewriting for `git@github.com:` remotes and submodules.
- Use `/home/codex/workshop` as the Codex working folder for vault/memo work. It is separate from the synced vault and has a local `.codex/config.toml` that grants write access to `/home/codex/vaults/dgr-collab`.
- `codex-workshop` starts Codex in `/home/codex/workshop` with `/home/codex/vaults/dgr-collab` added as a writable directory.
- Vaults on the box:
  - Main vault: `/home/codex/vaults/dgr`, cloned from private repo `dgrobinson/dgr-obsidian`, and intended as read-only source material.
  - Collaboration vault: `/home/codex/vaults/dgr-collab`, cloned from private repo `dgrobinson/dgr-collab`, and intended as the writable agent workspace.
- The local collab vault at `/Users/dgrobinson/vaults/dgr-collab` is backed by private GitHub repo `dgrobinson/dgr-collab`.
- `vault-mcp` is cloned on the box at `/home/codex/code/vault-mcp`, built with npm, and registered in remote Codex as MCP server `vault-mcp`.
- `dgr-collab` is vault content only. Do not add sync scripts, service files, binaries, or operational tooling to that repo; keep automation in dotfiles or machine-local service config.
- When Obsidian Headless Sync is configured for `dgr-collab`, treat Obsidian Sync as the live cross-device sync layer and GitHub as backup/audit only.
- Obsidian Headless is installed on `codex-box` at `/home/codex/.local/opt/obsidian-headless`, using a local Node 22 install so the system Node 20 runtime stays unchanged.
- The continuous live sync service is `obsidian-dgr-collab-sync.service`; inspect it with `systemctl status obsidian-dgr-collab-sync.service` and `journalctl -u obsidian-dgr-collab-sync.service`.
- The dotfiles helper `dgr-collab-sync` is backup-only: it commits stageable local vault changes and pushes them to `origin/main`; it refuses to pull or rebase GitHub changes back into the live vault.
- The GitHub backup timer is `dgr-collab-sync.timer`; it runs separately from Obsidian Headless and mirrors the live vault to GitHub every five minutes.
- Run only one automated Git backup bridge for `dgr-collab` at a time, preferably on `codex-box`, to avoid duplicate backup commits from multiple Obsidian-synced devices.
- DigitalOcean firewall `codex-box-ssh-only` allows inbound SSH only from the current trusted public IP. If SSH stops working after a network change, update that firewall rule rather than opening SSH broadly.
- `codex-box` is also joined to Tailscale as `codex-box` at `100.73.192.35`, for anywhere SSH access without opening public SSH broadly.
- SSH password authentication is enabled only for user `codex` from Tailscale source addresses (`100.64.0.0/10`) via the final block in `/etc/ssh/sshd_config`; public-source password SSH remains disabled.
- For ChatGPT mobile Codex SSH remotes, use host `100.73.192.35`, user `codex`, project folder `/home/codex/workshop`, and Codex command `/home/codex/.local/bin/codex`.
- `codex remote-control` requires the managed standalone install at `/home/codex/.codex/packages/standalone/current/codex`; `/usr/bin/codex` is the older npm-managed binary and should not be used for mobile remote setup.
- Billing guardrail: powered-off Droplets still bill because their resources remain reserved. Destroy `codex-box` when it is no longer needed, after confirming no needed work remains on the machine.
- Before assuming the cloud state, verify it:
  - `doctl compute droplet list`
  - `doctl databases list`
