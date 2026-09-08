#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Contextual Right Side
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Window Tiling
# @raycast.description On big landscape displays, alternate the front window between the right third and half; use the right half on smaller displays.
# @raycast.icon R

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${SCRIPT_DIR}/contextual-corner" right-side "$@"
