function set_iterm_window_title() {
  if [[ "$PWD" == "$HOME/code/agents/"* ]]; then
    echo -ne "\033]2;${PWD##*/}\007"
  fi
}

function set_iterm_window_badge() {
  if [[ "${TERM_PROGRAM:-}" != "iTerm.app" && -z "${ITERM_SESSION_ID:-}" ]]; then
    return
  fi

  local badge=""
  if [[ "$PWD" == "$HOME/code" || "$PWD" == "$HOME/code/"* ]]; then
    if (( ${+functions[repo_relpath]} )); then
      badge="$(repo_relpath)"
    else
      badge="${PWD/#$HOME/~}"
    fi
  fi

  if command -v base64 >/dev/null 2>&1; then
    local encoded
    encoded=$(printf %s "$badge" | base64 | tr -d '\n')
    printf '\033]1337;SetBadgeFormat=%s\007' "$encoded"
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd set_iterm_window_title
add-zsh-hook chpwd set_iterm_window_badge
set_iterm_window_title




# Common Zsh configuration
# Shared between work and personal environments

# Disable audible bell
setopt NO_BEEP

# Oh My Zsh installation
export ZSH="$HOME/.oh-my-zsh"
export ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/oh-my-zsh"

# Theme
ZSH_THEME="robbyrussell-fullpath"

# Oh My Zsh settings
HIST_STAMPS="yyyy-mm-dd"
COMPLETION_WAITING_DOTS="true"

# Plugins (common ones that are useful everywhere)
plugins=(
  git
  docker
  docker-compose
  npm
  yarn
  python
  pip
  golang
  rust
  fzf
  z
  colored-man-pages
  command-not-found
  copyfile
  copypath
  encode64
  extract
  jsontools
  urltools
  web-search
)

# Load Oh My Zsh
source $ZSH/oh-my-zsh.sh
set_iterm_window_badge

#------------------------------
# Common aliases
#------------------------------
# Navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'

# List files
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gpl='git pull'
alias gco='git checkout'
alias gb='git branch'
alias glog='git log --oneline --graph --decorate'

# Safety aliases
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Utility aliases
alias h='history'
alias j='jobs -l'
alias which='type -a'
alias path='echo -e ${PATH//:/\\n}'
alias now='date +"%Y-%m-%d %T"'
alias timestamp='date +%s'

# Directory shortcuts
alias dl="cd ~/Downloads"
alias dt="cd ~/Desktop"
alias docs="cd ~/Documents"

# Quick edit configs
alias vimrc='vim ~/.vimrc'
alias zshrc='vim ~/.zshrc'

#------------------------------
# Common functions
#------------------------------
# Create directory and cd into it
mkcd() {
  mkdir -p "$1" && cd "$1"
}

# Extract various archive types
extract() {
  if [ -f $1 ]; then
    case $1 in
      *.tar.bz2)   tar xjf $1     ;;
      *.tar.gz)    tar xzf $1     ;;
      *.bz2)       bunzip2 $1     ;;
      *.rar)       unrar e $1     ;;
      *.gz)        gunzip $1      ;;
      *.tar)       tar xf $1      ;;
      *.tbz2)      tar xjf $1     ;;
      *.tgz)       tar xzf $1     ;;
      *.zip)       unzip $1       ;;
      *.Z)         uncompress $1  ;;
      *.7z)        7z x $1        ;;
      *)           echo "'$1' cannot be extracted via extract()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}

# Find process by name
findprocess() {
  ps aux | grep -v grep | grep -i "$1"
}

# Get current git branch
git_branch() {
  git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

#------------------------------
# Environment variables
#------------------------------
# Editor
export EDITOR='vim'
export VISUAL='vim'

# Language
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# History
export HISTSIZE=10000
export SAVEHIST=10000
export HISTFILE=~/.zsh_history

# Less
export LESS='-R'

# Colors for ls
export LSCOLORS="ExGxBxDxCxEgEdxbxgxcxd"
export CLICOLOR=1

#------------------------------
# PATH additions (common tools)
#------------------------------
# Add common binary directories if they exist
[[ -d "/usr/local/bin" ]] && export PATH="/usr/local/bin:$PATH"
[[ -d "$HOME/.local/bin" ]] && export PATH="$HOME/.local/bin:$PATH"
[[ -d "$HOME/bin" ]] && export PATH="$HOME/bin:$PATH"

# Programming language specific paths
# Node.js
[[ -d "$HOME/.npm-global/bin" ]] && export PATH="$HOME/.npm-global/bin:$PATH"

# Python
[[ -d "$HOME/.poetry/bin" ]] && export PATH="$HOME/.poetry/bin:$PATH"

# Rust
[[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"

# Go
[[ -d "/usr/local/go/bin" ]] && export PATH="/usr/local/go/bin:$PATH"
[[ -d "$HOME/go/bin" ]] && export PATH="$HOME/go/bin:$PATH"

#------------------------------
# Completion settings
#------------------------------
autoload -Uz compinit
compinit

# Case insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# Colorful completion
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

#------------------------------
# Key bindings
#------------------------------
# Enable vim mode
bindkey -v

# But keep some emacs bindings
bindkey '^P' up-history
bindkey '^N' down-history
bindkey '^A' beginning-of-line
bindkey '^E' end-of-line
bindkey '^K' kill-line
bindkey '^R' history-incremental-search-backward

#------------------------------
# FZF configuration (if installed)
#------------------------------
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

#------------------------------
# Claude local installation alias (if local installation exists)
#------------------------------
if [ -f "$HOME/.claude/local/claude" ]; then
    alias claude="$HOME/.claude/local/claude"
fi

#------------------------------
# Local customization
#------------------------------
# Legacy extension point:
#   - ~/.zshrc.local (sourced if present)
# Recommended explicit layering (see README):
#   - ~/.zshrc.common (this file)
#   - ~/.zshrc.work or ~/.zshrc.home
#   - ~/.zshrc.secrets (untracked)
[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local
