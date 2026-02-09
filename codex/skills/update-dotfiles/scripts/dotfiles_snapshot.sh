#!/usr/bin/env bash
set -euo pipefail

input_root="${1:-}"

if [[ -n "$input_root" ]]; then
  wrapper_root="$(cd "$input_root" && pwd)"
else
  wrapper_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi

if [[ -z "$wrapper_root" ]]; then
  echo "ERROR: could not detect repo root; run from the wrapper repo or pass root path." >&2
  exit 2
fi

if [[ "$(basename "$wrapper_root")" == "common" && -d "$wrapper_root/.." ]]; then
  wrapper_root="$(cd "$wrapper_root/.." && pwd)"
fi

common_root="$wrapper_root/common"

if [[ ! -d "$common_root" ]]; then
  echo "ERROR: expected common submodule at $common_root" >&2
  exit 2
fi

detect_profile() {
  if [[ -n "${DOTFILES_PROFILE:-}" && -d "$wrapper_root/$DOTFILES_PROFILE" ]]; then
    printf '%s\n' "$DOTFILES_PROFILE (from DOTFILES_PROFILE)"
    return 0
  fi

  local has_work=0
  local has_home=0
  [[ -d "$wrapper_root/work" ]] && has_work=1
  [[ -d "$wrapper_root/home" ]] && has_home=1

  if [[ "$has_work" -eq 1 && "$has_home" -eq 0 ]]; then
    printf '%s\n' "work (only overlay present)"
    return 0
  fi
  if [[ "$has_home" -eq 1 && "$has_work" -eq 0 ]]; then
    printf '%s\n' "home (only overlay present)"
    return 0
  fi

  if [[ -L "$HOME/.zshrc.work" ]]; then
    local work_target
    work_target="$(cd "$(dirname "$HOME/.zshrc.work")" && pwd)/$(readlink "$HOME/.zshrc.work")"
    work_target="$(cd "$(dirname "$work_target")" && pwd)/$(basename "$work_target")"
    if [[ "$work_target" == "$wrapper_root/work/"* ]]; then
      printf '%s\n' "work (from ~/.zshrc.work symlink)"
      return 0
    fi
  fi

  if [[ -L "$HOME/.zshrc.home" ]]; then
    local home_target
    home_target="$(cd "$(dirname "$HOME/.zshrc.home")" && pwd)/$(readlink "$HOME/.zshrc.home")"
    home_target="$(cd "$(dirname "$home_target")" && pwd)/$(basename "$home_target")"
    if [[ "$home_target" == "$wrapper_root/home/"* ]]; then
      printf '%s\n' "home (from ~/.zshrc.home symlink)"
      return 0
    fi
  fi

  printf '%s\n' "ambiguous (set DOTFILES_PROFILE=work|home)"
}

print_changes() {
  local repo="$1"
  local label="$2"

  echo
  echo "[$label] branch"
  git -C "$repo" branch --show-current

  echo
  echo "[$label] status --short"
  git -C "$repo" status --short || true

  echo
  echo "[$label] unstaged paths"
  git -C "$repo" diff --name-only || true

  echo
  echo "[$label] staged paths"
  git -C "$repo" diff --cached --name-only || true

  echo
  echo "[$label] untracked paths"
  git -C "$repo" ls-files --others --exclude-standard || true
}

echo "Wrapper root: $wrapper_root"
echo "Common root:  $common_root"
echo "Profile:      $(detect_profile)"

print_changes "$wrapper_root" "wrapper"
print_changes "$common_root" "common"
