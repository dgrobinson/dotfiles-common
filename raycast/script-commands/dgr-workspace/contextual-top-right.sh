#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Upper Right
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description Send the front window to the upper-right sixth on big displays or upper-right quarter on smaller displays.
# @raycast.icon UR

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" top-right "$@"
