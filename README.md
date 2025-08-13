# Common Dotfiles

This repository contains shared configuration files used across both work and personal environments.

## Contents

- **vim/**: Common Vim configuration and plugins
- **zsh/**: Common Zsh configuration, oh-my-zsh, and aliases
- **git/**: Common Git configuration and global gitignore
- **cursor/**: Cursor editor settings and themes

## Usage

This repository is designed to be used as a git submodule in environment-specific wrapper repositories:

- Personal: `github.com/dgrobinson/dgr-dotfiles`
- Work: `github.com/dgrobinson-oai/dgr-settings-work`

### Adding to a wrapper repository

```bash
git submodule add -b main git@github.com:dgrobinson/dotfiles-common.git common
```

### Updating common files

```bash
cd common
git pull origin main
cd ..
git add common
git commit -m "Update common submodule"
```

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
- Zsh: Sources `~/.zshrc.local` for environment-specific settings
- Git: Includes `~/.gitconfig.local` for user-specific configuration

Wrapper repositories typically just symlink these local files from their `work/` or `personal/` areas and keep `~/.vimrc`, `~/.zshrc`, and `~/.gitconfig` pointing at common.

## Security

Run `./setup-hooks.sh` to install a pre-commit hook that prevents accidentally committing sensitive data like API keys, passwords, or work-specific content to the common dotfiles.