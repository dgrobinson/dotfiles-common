setopt promptsubst

repo_relpath() {
  local root rel
  root=$(git rev-parse --show-toplevel 2>/dev/null) || { print -r -- "${PWD/#$HOME/~}"; return; }
  if [[ "$PWD" == "$root" ]]; then
    print -r -- "$(basename "$root")"
  else
    rel="${PWD#$root/}"
    print -r -- "$(basename "$root")/$rel"
  fi
}

ZSH_THEME_GIT_PROMPT_PREFIX="%{$fg_bold[magenta]%}git:(%{$fg[red]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%})"
ZSH_THEME_GIT_PROMPT_DIRTY=" %{$fg[red]%}✗%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_CLEAN=" %{$fg[green]%}✓%{$reset_color%}"

# Robby Russell style with dynamic repo path
# PROMPT=$'\n'"%F{brightcyan}\$(repo_relpath)%f %{$fg_bold[magenta]%}\$(git_prompt_info)%{$reset_color%}%{$fg_bold[blue]%} %# %{$reset_color%}"


PROMPT="%{$fg_bold[green]%}➜ %F{brightcyan}\$(repo_relpath)%f %{$fg_bold[magenta]%}\$(git_prompt_info)%{$reset_color%} "