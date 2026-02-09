# Dotfiles Routing Rules

Use this file to decide where a change belongs before editing.

## Primary Rule

If the setting only makes sense for one environment, keep it in that environment overlay.

- Work-only/OpenAI-specific behavior: `work/`
- Home-only behavior: `home/`
- Shared behavior across environments: `common/`

## Path Routing

- `work/**`: Work overlay files for this wrapper repo.
- `home/**`: Home overlay files for this wrapper repo.
- `common/**`: Shared defaults and tooling in the common submodule.
- `install.sh`, `bin/**`, top-level `AGENTS.md`: Wrapper glue and workflow docs for this wrapper.
- `common/codex/skills/**`: Shared Codex skills; prefer this for skills you want in both environments.

## Commit Routing

If you changed files in `common/`:

1) Commit in `common`:
```bash
git -C common add <paths>
git -C common commit -m "<message>"
git -C common push origin main
```

2) Then commit pointer update in wrapper:
```bash
git add common
git commit -m "Update common submodule"
```

If you changed only `work/` or `home/`, commit in wrapper repo only.

## Keep Unrelated Work Safe

- Avoid stash/autostash/reset.
- Stage exact paths, not broad globs.
- Leave unrelated modified files unstaged unless explicitly requested.
