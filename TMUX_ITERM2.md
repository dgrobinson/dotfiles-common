# iTerm2 agent batches (manual setup)

`codexplex` now only creates/updates worktrees and prints per-worktree commands.
Open iTerm2 windows or splits manually and run the printed commands in each one.

## Prereqs

- iTerm2 installed.
- Run commands from a normal shell (any directory is fine).

## Quick start (single command)

Run from iTerm2:

```
cd "$HOME/code/dgr-dotfiles" && codexplex docs/batches/anchor --repo . --agents 3
```

This creates worktrees under `docs/batches/anchor` and prints one command per
worktree to launch Codex.

## Workflow

1. Run `codexplex` to create/update worktrees (see examples below).
2. Open one iTerm2 window or split per worktree.
3. Paste the matching command for each worktree (printed by `codexplex`).

## One-shot setup (clone + worktrees)

If you want the script to clone the repo and create agent worktrees:

```
codexplex ~/code/article-monster/docs/batches/01-anchor \
  --repo git@github.com:your-org/article-monster.git \
  --agents 6
```

This creates a source clone at `~/code/article-monster/docs/batches/01-anchor/.source`
and worktrees like `agent-01`, `agent-02`, etc.

## Smoke test (worktrees + manual launch)

Goal: confirm worktree setup and that the printed commands set the expected
variables.

Run:

```
codexplex "$PWD/docs/batches/anchor" \
  --repo "$PWD" \
  --agents 3 \
  --cmd 'pwd; echo "WORKTREE=$CODEX_WORKTREE NAME=$CODEX_WORKTREE_NAME"; git rev-parse --abbrev-ref HEAD; sleep 9999'
```

In each iTerm2 window, paste the matching command printed by `codexplex`, then
verify:
- `pwd` and `CODEX_WORKTREE` match the worktree directory.
- Terminal output shows the expected `agent-01`, `agent-02`, etc.
- Branch names are `agent/agent-01`, `agent/agent-02`, etc (unless `--detach` is used).

Cleanup:
```
rm -rf docs/batches/anchor
# or archive: mv docs/batches/anchor docs/archived/anchor
```

## Mixed local + cloud commands

Use `--cmd-map` to mix local Codex sessions with cloud exec commands. The map
format is one entry per line: `<worktree-name> <command>`.

Example:
```
cat > /tmp/agents.cmds <<'EOF'
agent-01 codex begin
agent-02 codex cloud exec --env <env-name>
agent-03 codex begin
EOF

codexplex "$PWD/docs/batches/anchor" --cmd-map /tmp/agents.cmds
```

## Helper script

Location: `common/bin/codexplex` (deprecated alias: `codex-batch-panes`)

Key options:
- `--repo <url-or-path>` to clone and manage worktrees under `<batch-dir>/.source`
- `--agents 6` to create N worktrees (default names `agent-01`, `agent-02`, ...)
- `--names agent-a,agent-b` to create explicit worktree names
- `--branch main` to choose a base branch/ref for new worktrees
- `--branch-prefix agents/` to control per-agent branch names
- `--detach` to create detached worktrees instead of per-agent branches
- `--cmd "codex begin"` to override the command in the printed instructions
- `--cmd-map <file>` to override commands per worktree
- `--safe` to use default codex config (`codex begin`)

Notes:
- The script detects worktrees by looking for subdirectories that contain
  `.git` (directory or file).
- The script resolves the batch directory to an absolute path before creating
  worktrees, which avoids nesting worktrees under `.source` when you pass a
  relative batch path.
- The printed commands export `CODEX_PROJECT_ROOT` to the batch directory
  (keeps `.source` inside the workspace-write sandbox) and set
  `CODEX_WORKTREE`/`CODEX_WORKTREE_NAME` to the specific worktree.
- Legacy tmux flags (for example `--iterm2`) are ignored.

## Troubleshooting

- `error: worktree missing`: rerun `codexplex` with `--agents`/`--names`, or
  inspect the batch directory for stray folders.
- `error: base ref not found`: pass `--branch` to select a valid base branch.
- If you accidentally created a batch directory with a newline (copy/paste issue),
  list it with `ls -lab docs/batches` and move it out of the repo. Safe cleanup helper:
  ```
  python3 - <<'PY'
  import os, shutil, time
  root = "docs/batches"
  stamp = time.strftime("%Y%m%d-%H%M%S")
  trash = f"/private/tmp/dgr-dotfiles-batches-trash-{stamp}"
  os.makedirs(trash, exist_ok=True)
  for name in os.listdir(root):
      if any(ch in name for ch in "\n\r\t"):
          shutil.move(os.path.join(root, name), os.path.join(trash, name.replace("\n", "\\n")))
  print(trash)
  PY
  ```
