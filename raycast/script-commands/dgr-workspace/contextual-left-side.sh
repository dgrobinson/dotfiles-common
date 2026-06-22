#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Left Side
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description Send the front window to the left third on big displays or left half on smaller displays.
# @raycast.icon L

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" left-side "$@"
