#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $(basename "$0") <theme-name>" >&2
  echo "Example: $(basename "$0") dracula" >&2
  echo "" >&2
  echo "Optional: set CURSOR_SETTINGS to override the settings.json path." >&2
  exit 1
fi

name="$1"
theme_file="$here/themes/${name%.json}.json"

if [[ ! -f "$theme_file" ]]; then
  echo "Theme not found: $theme_file" >&2
  echo "Available themes:" >&2
  ls -1 "$here"/themes/*.json 2>/dev/null | xargs -n1 basename | sed 's/\.json$//' || true
  exit 1
fi

# Detect Cursor settings path
settings="${CURSOR_SETTINGS:-}"
if [[ -z "$settings" ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then
    settings="$HOME/Library/Application Support/Cursor/User/settings.json"
  else
    # Assume Linux
    settings="$HOME/.config/Cursor/User/settings.json"
  fi
fi

if [[ ! -f "$settings" ]]; then
  echo "Cursor settings not found at: $settings" >&2
  echo "Open Cursor once to generate it, then re-run." >&2
  exit 1
fi

ts="$(date +%Y%m%d-%H%M%S)"
backup_dir="$(dirname "$settings")"
backup_file="$backup_dir/settings.json.bak.$ts"
cp "$settings" "$backup_file"
echo "Backed up settings to: $backup_file"

python3 - "$settings" "$theme_file" <<'PY'
import json
import os
import sys
import tempfile
from pathlib import Path

settings_link = Path(sys.argv[1])
theme_path = Path(sys.argv[2])

def strip_jsonc(text: str) -> str:
    # Remove //... and /*...*/ comments while respecting strings.
    out = []
    i = 0
    n = len(text)
    in_str = False
    str_char = '"'
    escape = False
    in_line = False
    in_block = False

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_line:
            if c == "\n":
                in_line = False
                out.append(c)
            i += 1
            continue

        if in_block:
            if c == "*" and nxt == "/":
                in_block = False
                i += 2
            else:
                i += 1
            continue

        if in_str:
            out.append(c)
            if escape:
                escape = False
            else:
                if c == "\\":
                    escape = True
                elif c == str_char:
                    in_str = False
            i += 1
            continue

        if c in ('"', "'"):
            in_str = True
            str_char = c
            out.append(c)
            i += 1
            continue

        if c == "/" and nxt == "/":
            in_line = True
            i += 2
            continue

        if c == "/" and nxt == "*":
            in_block = True
            i += 2
            continue

        out.append(c)
        i += 1

    return "".join(out)

def strip_trailing_commas(text: str) -> str:
    # Remove trailing commas before } or ] while respecting strings.
    out = []
    i = 0
    n = len(text)
    in_str = False
    str_char = '"'
    escape = False

    while i < n:
        c = text[i]

        if in_str:
            out.append(c)
            if escape:
                escape = False
            else:
                if c == "\\":
                    escape = True
                elif c == str_char:
                    in_str = False
            i += 1
            continue

        if c in ('"', "'"):
            in_str = True
            str_char = c
            out.append(c)
            i += 1
            continue

        if c == ",":
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in "}]":
                i += 1
                continue

        out.append(c)
        i += 1

    return "".join(out)

def load_jsonish(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("\ufeff"):
        raw = raw.lstrip("\ufeff")
    cleaned = strip_trailing_commas(strip_jsonc(raw)).strip()
    if not cleaned:
        return {}
    return json.loads(cleaned)

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)

try:
    settings_real = settings_link.resolve()
    settings_obj = load_jsonish(settings_real)
except Exception as e:
    die(f"Failed to parse Cursor settings as JSON/JSONC: {settings_link} ({e})")

try:
    theme_obj = load_jsonish(theme_path.resolve())
except Exception as e:
    die(f"Failed to parse theme JSON: {theme_path} ({e})")

# Replace or create these customization objects; leave everything else intact.
for k in ("workbench.colorCustomizations", "editor.tokenColorCustomizations"):
    if k in theme_obj:
        settings_obj[k] = theme_obj[k]

out_text = json.dumps(settings_obj, indent=2, sort_keys=False) + "\n"

try:
    mode = settings_real.stat().st_mode & 0o777
except FileNotFoundError:
    mode = 0o644

fd, tmp = tempfile.mkstemp(
    dir=str(settings_real.parent),
    prefix=settings_real.name + ".",
    suffix=".tmp",
)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(out_text)
    os.chmod(tmp, mode)
    os.replace(tmp, settings_real)
finally:
    try:
        os.unlink(tmp)
    except FileNotFoundError:
        pass
PY

echo "Applied theme: $name"
echo "Restart Cursor if changes do not appear immediately."
