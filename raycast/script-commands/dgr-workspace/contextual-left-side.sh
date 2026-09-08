#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Left Side
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description On big landscape displays, alternate the front window between the left third and half; use the left half on smaller displays.
# @raycast.icon L

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" left-side "$@"
