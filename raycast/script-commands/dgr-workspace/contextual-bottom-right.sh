#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Bottom Right
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description Send the front window to the bottom-right sixth on big displays or bottom-right quarter on smaller displays.
# @raycast.icon BR

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" bottom-right "$@"
