# Backwards-compatibility shim.
#
# Historically wrappers symlinked `~/.zshrc -> common/zsh/.zshrc`.
# The recommended model now uses:
#   - `~/.zshrc`         (dispatcher)
#   - `~/.zshrc.common`  (symlink to common config)
#   - `~/.zshrc.work` / `~/.zshrc.home`
#   - `~/.zshrc.secrets` (untracked)
#
# Keep this file so older setups continue to work, but delegate to the
# explicitly-named common config file living alongside it.

_zsh_common_dir="${${(%):-%N}:A:h}"
[[ -f "$_zsh_common_dir/.zshrc.common" ]] && source "$_zsh_common_dir/.zshrc.common"
unset _zsh_common_dir

