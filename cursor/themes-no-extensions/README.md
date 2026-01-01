Cursor Themes (No Extensions)

This folder provides a small set of curated color theme JSON overrides you can apply to Cursor without installing any extensions. The apply script merges these overrides into your Cursor `settings.json` and backs up the original first.

Why this approach
- No extensions installed; only settings are changed
- JSON is versioned in this repo for transparency
- Script makes a timestamped backup before changes

How to use
- List themes: `ls themes/*.json`
- Apply a theme (macOS/Linux): `./apply_theme.sh dracula` (name matches the JSON file)
- Revert: copy the most recent `settings.json.bak.<timestamp>` back to `settings.json`

Notes
- The overrides use `workbench.colorCustomizations` and `editor.tokenColorCustomizations`. They work with any base theme, but results may vary slightly.
- Requires `python3` (standard on macOS/Linux). The script rewrites `settings.json` as strict JSON (comments removed).
- If your `settings.json` is symlinked into a dotfiles repo, applying a theme updates the symlink target (you may see a git diff).
- macOS settings path: `~/Library/Application Support/Cursor/User/settings.json`
- Linux settings path: `~/.config/Cursor/User/settings.json`
- Override settings path: set `CURSOR_SETTINGS=/path/to/settings.json`
