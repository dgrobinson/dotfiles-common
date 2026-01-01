# Codex Agent Instructions

This file is my global guidance for Codex (applies across repos).
Do not add secrets here.

## Spend tracking

Use the `openai-usage` wrapper for any task expected to cost more than $1.

Workflow:
- Before starting: `openai-usage --delta --label "<repo>:<task>"`
- After finishing: run the same command with the same label.
- Report the delta in the final response.
  - If network access is restricted or the command fails due to DNS, rerun the
    `openai-usage` call with escalated permissions to allow network access.

Label guidance:
- Use `<repo>:<task>` as the base label.
- If you rerun the same task, append a short run id (e.g. `<repo>:<task>:2025-02-01a`) and reuse it for both before/after calls.

## Repo layout: template clone + git worktrees (preferred)

ELI5: A `git worktree` is an extra working folder that shares the same underlying git history as a base clone.
This is faster and lighter than re-cloning a repo for every task/branch.

Conventions:
- Keep one "template" clone per repo that you do not edit day-to-day.
  - Use it as the control center for creating/removing worktrees.
- Create one worktree per task/branch as a sibling directory.
  - Worktrees share git objects (fast), but they do NOT share dependency installs (you still run `npm ci`, `pip install`, etc per worktree).

Common commands (run from the template clone):
- Refresh remote refs: `git fetch origin`
- New worktree on a new branch:
  - `git worktree add ../wt-my-task -b dgr/my-task origin/main`
- Worktree for an existing branch:
  - `git worktree add ../wt-my-task dgr/my-task`
- List worktrees: `git worktree list`
- Remove a worktree directory when done:
  - `git worktree remove ../wt-my-task`
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
