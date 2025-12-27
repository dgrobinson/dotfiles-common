# Codex Agent Instructions

## Spend tracking

Use the `openai-usage` wrapper for any task expected to cost more than $1.

Workflow:
- Before starting: `openai-usage --delta --label "<repo>:<task>"`
- After finishing: run the same command with the same label.
- Report the delta in the final response.

Label guidance:
- Use `<repo>:<task>` as the base label.
- If you rerun the same task, append a short run id (e.g. `<repo>:<task>:2025-02-01a`) and reuse it for both before/after calls.

## Batch panes / worktrees

- If `CODEX_WORKTREE` is set, treat it as the project root for all file ops.
- Use `CODEX_WORKTREE_NAME` to label outputs or logs when multiple agents run.
- `codex-batch-panes` creates worktrees under a batch directory and launches
  `codex -a never -s danger-full-access begin` in each pane by default.
- If you need the git root, prefer `git -C "$CODEX_WORKTREE" rev-parse --show-toplevel`.

## Batch work structure

- Batch tasks should be parallelizable; avoid sequencing dependencies between briefs in the same batch.
- Name batches as a themed series (e.g., trees: arbor, birch, cypress; nautical: anchor, bowline, compass).
- Track each batch under `docs/batches/<batch-name>` at the repo root while work is active.
- When a batch is complete, move its record to `docs/archived/<batch-name>`.
