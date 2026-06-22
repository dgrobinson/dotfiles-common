#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Bottom Left
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description Send the front window to the bottom-left sixth on big displays or bottom-left quarter on smaller displays.
# @raycast.icon BL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" bottom-left "$@"
