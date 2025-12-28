# Common Dotfiles

This repository contains shared configuration files used across both work and personal environments.

## Contents

- **vim/**: Common Vim configuration and plugins
- **zsh/**: Common Zsh configuration, oh-my-zsh, and aliases
- **git/**: Common Git configuration and global gitignore
- **cursor/**: Cursor editor settings and themes

## Usage

This repository is designed to be used as a git submodule inside one or more environment-specific wrapper repositories (for example, a personal wrapper and a work wrapper). The wrapper repo typically contains only local overlays and a small installer/symlink script.

- Personal: `github.com/dgrobinson/dgr-dotfiles`
- Work: `github.com/dgrobinson-oai/dgr-settings-work`

### Adding to a wrapper repository

```bash
git submodule add -b main git@github.com:dgrobinson/dotfiles-common.git <submodule-path>
```

### Updating common files

```bash
cd <submodule-path>
git pull origin main
cd ..
git add <submodule-path>
git commit -m "Update common submodule"
```

### Keeping wrappers in sync (important)

Git submodules are pinned: each wrapper repository records an exact `dotfiles-common` commit SHA. That means:

- If you commit + push a change to `dotfiles-common`, it will not automatically appear in your wrapper repos until you update the submodule pointer there.
- `git pull --recurse-submodules` updates the submodule checkout to whatever commit the wrapper currently points at; it does not advance to the latest `dotfiles-common/main` by itself.

Recommended (reproducible) workflow when you have multiple wrappers:

1) Make your change in `dotfiles-common` and push it.
2) In each wrapper repo, update the submodule to the new commit and commit the updated pointer in the wrapper.

If you prefer a "floating" wrapper that always tracks the latest `dotfiles-common/main` without committing the pointer, you can run `git submodule update --remote --checkout <submodule-path>` on that machine. This is convenient but less deterministic.

### Making changes from inside a wrapper checkout

When `dotfiles-common` is checked out as a submodule, Git often leaves it in a detached HEAD. Before committing, switch to a branch that tracks `origin/main`:

```bash
cd <wrapper-repo>/<submodule-path>
git fetch origin
git switch -c my-change origin/main   # or `git switch main` if you already have it tracking

# edit files...
git add -A
git commit -m "Describe the change"
git push origin HEAD:main
```

Then update the wrapper's submodule pointer:

```bash
cd <wrapper-repo>
git submodule update --remote --checkout <submodule-path>
git add <submodule-path>
git commit -m "chore(submodule): bump dotfiles-common"
git push
```

Avoid running automatic pulls on shell startup; prefer an explicit "sync" command/script so changes don't surprise you mid-session.

## Philosophy

- Only files that are safe to share between environments go here
- No secrets, API keys, or environment-specific paths
- Configuration should work on macOS and Linux
- Prefer simplicity and portability

## Local Customization

This repository is wrapper-friendly and provides explicit extension points so you do not need to modify the submodule to customize per-environment:

- Vim:
  - Put settings/mappings in `~/.vimrc.local`
  - Optional modular overrides in `~/.vimrc.d/*.vim` (loaded in sorted order)
  - Optional extra plugins in `~/.vimrc.plugins` (only `Plugin 'owner/repo'` lines)
  - Theme: set `let g:preferred_colorscheme = 'your-theme'` in `~/.vimrc.local`; falls back to `gruvbox`/`default` if unavailable
- Zsh:
  - Legacy extension point: `~/.zshrc.local` (sourced by the common `~/.zshrc` if present)
  - Recommended explicit layering for "work + home" setups:
    - `~/.zshrc.common` (symlink to `zsh/.zshrc.common` in this repo; `zsh/.zshrc` is a compatibility shim)
    - `~/.zshrc.work` / `~/.zshrc.home` (machine-specific overrides)
    - `~/.zshrc.secrets` (untracked; API keys/tokens)
- Git: Includes `~/.gitconfig.local` for user-specific configuration

Wrapper repositories typically just symlink these local files from their `work/` or `personal/` areas and keep `~/.vimrc`, `~/.zshrc`, and `~/.gitconfig` pointing at common.

Example `~/.zshrc` dispatcher for a two-machine setup:

```zsh
# Shared config from the common repo
[[ -f ~/.zshrc.common ]] && source ~/.zshrc.common

# Untracked secrets (optional)
[[ -f ~/.zshrc.secrets ]] && source ~/.zshrc.secrets

# Machine-specific config (only one should exist per machine)
[[ -f ~/.zshrc.work ]] && source ~/.zshrc.work
[[ -f ~/.zshrc.home ]] && source ~/.zshrc.home
```

## Security

Run `./setup-hooks.sh` to install a pre-commit hook that prevents accidentally committing sensitive data like API keys, passwords, or work-specific content to the common dotfiles.
