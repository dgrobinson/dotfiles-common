#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Right Side
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description Send the front window to the right third on big displays or right half on smaller displays.
# @raycast.icon R

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" right-side "$@"
