# iTerm2 + tmux for agent batches

This setup uses tmux to create and manage panes, while iTerm2 renders them as
native splits when you attach with tmux integration (`tmux -CC`).

## iTerm2 settings

1. Preferences > General > Enable tmux integration.
2. Preferences > General > "When attaching to a tmux session" > Tabs in attaching window.
3. Preferences > Appearance > Dimming > Dim inactive split panes.

## Prereqs

- Install tmux: `brew install tmux`
- Run commands from a full-screen iTerm2 window (not already inside tmux).

## Quick start (single command)

Run from iTerm2 (any directory is fine):

```
cd "$HOME/code/dgr-dotfiles" && codex-batch-panes docs/batches/anchor --repo . --agents 3 --iterm2 --replace
```

This creates worktrees under `docs/batches/anchor`, opens matching panes, and
auto-starts `codex -a never -s danger-full-access begin` in each pane.

## Workflow

1. Ensure your batch worktrees exist, for example:
   `~/code/article-monster/docs/batches/01-anchor/agent-*`
2. Run the helper script from a normal shell in iTerm2 (not already inside tmux):
   `codex-batch-panes ~/code/article-monster/docs/batches/01-anchor --iterm2`
3. Each pane starts in its worktree and runs
   `codex -a never -s danger-full-access begin`.

## One-shot setup (clone + worktrees)

If you want the script to clone the repo and create agent worktrees:

```
codex-batch-panes ~/code/article-monster/docs/batches/01-anchor \
  --repo git@github.com:your-org/article-monster.git \
  --agents 6 \
  --iterm2
```

This creates a source clone at `~/code/article-monster/docs/batches/01-anchor/.source`
and worktrees like `agent-01`, `agent-02`, etc.

## Smoke test (worktrees + iTerm2 auto-start)

Goal: confirm worktree setup and that each iTerm2 pane runs the command.

Run from a normal shell in iTerm2 (not already inside tmux):

```
codex-batch-panes "$PWD/docs/batches/anchor" \
  --repo "$PWD" \
  --agents 3 \
  --iterm2 \
  --replace \
  --cmd 'pwd; echo "WORKTREE=$CODEX_WORKTREE NAME=$CODEX_WORKTREE_NAME"; git rev-parse --abbrev-ref HEAD; sleep 9999'
```

Verify:
- iTerm2 shows native split panes (tmux -CC).
- Pane titles match worktree dirs (`agent-01`, `agent-02`, `agent-03`).
- `pwd` and `CODEX_WORKTREE` match the pane's worktree directory.
- Branch names are `agent/agent-01`, `agent/agent-02`, etc (unless `--detach` is used).

Optional (Codex auto-start check):
```
codex-batch-panes "$PWD/docs/batches/anchor" --iterm2 --replace
```

Cleanup:
```
tmux kill-session -t anchor
rm -rf docs/batches/anchor
# or archive: mv docs/batches/anchor docs/archived/anchor
```

## Reattach later

Use iTerm2 integration to get native panes:
`tmux -CC attach -t anchor`

## Helper script

Location: `common/bin/codex-batch-panes`

Key options:
- `--repo <url-or-path>` to clone and manage worktrees under `<batch-dir>/.source`
- `--agents 6` to create N worktrees (default names `agent-01`, `agent-02`, ...)
- `--names agent-a,agent-b` to create explicit worktree names
- `--branch main` to choose a base branch/ref for new worktrees
- `--branch-prefix agents/` to control per-agent branch names
- `--detach` to create detached worktrees instead of per-agent branches
- `--cmd "codex begin"` to override the command per pane
- `--safe` to use default codex config (`codex begin`)
- `--layout tiled` to change layout
- `--no-attach` if you are already inside tmux
- `--replace` to discard an existing session and recreate it

Notes:
- The script detects worktrees by looking for subdirectories that contain
  `.git` (directory or file).
- The script resolves the batch directory to an absolute path before creating
  worktrees, which avoids nesting worktrees under `.source` when you pass a
  relative batch path.
- The script exports `CODEX_PROJECT_ROOT`, `CODEX_WORKTREE`, and
  `CODEX_WORKTREE_NAME` in each pane before launching Codex.
- If you want `tmux -CC` by default for manual use, you can also set
  `ZSH_TMUX_ITERM2=true` in your shell config.

## Troubleshooting

- `tmux: command not found`: install tmux with `brew install tmux`.
- "Gibberish" output after using `--iterm2`: tmux control-mode is being printed.
  Confirm iTerm2 tmux integration is enabled, then retry in a new iTerm2 window.
  As a fallback, rerun without `--iterm2`.
- `error: worktree missing`: rerun with `--replace`. If you accidentally created
  a batch directory with a newline (copy/paste issue), list it with
  `ls -lab docs/batches` and move it out of the repo. Safe cleanup helper:
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
