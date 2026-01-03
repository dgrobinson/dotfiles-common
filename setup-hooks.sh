#!/usr/bin/env bash
# Set up git hooks for the common dotfiles repository

REPO_ROOT=$(cd "$(dirname "$0")"; pwd)
# Handle both regular repos and submodules
if [ -f "$REPO_ROOT/.git" ]; then
    # It's a submodule, extract the gitdir path
    GITDIR=$(cat "$REPO_ROOT/.git" | sed 's/gitdir: //')
    if [[ "$GITDIR" =~ ^\.\./ ]]; then
        # Relative path, resolve it
        GITDIR="$REPO_ROOT/$GITDIR"
    fi
    HOOKS_DIR="$GITDIR/hooks"
else
    # Regular repository
    HOOKS_DIR="$REPO_ROOT/.git/hooks"
fi

mkdir -p "$HOOKS_DIR"

cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/usr/bin/env bash
# Pre-commit hook to prevent committing sensitive files to common dotfiles

# Patterns that should never be in common dotfiles
FORBIDDEN_PATTERNS=(
    "oai"
    "openai"
    "api[_-]?key"
    "secret"
    "password"
    "private[_-]?key"
    "id_rsa"
    "id_ed25519"
    "\.pem$"
    "\.key$"
    "work/"
    "home/"
    "personal/"
)

# Check for forbidden patterns in filenames
for file in $(git diff --cached --name-only); do
    for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
        if echo "$file" | grep -iE "$pattern" > /dev/null; then
            echo "ERROR: File '$file' contains forbidden pattern '$pattern'"
            echo "Common dotfiles should not contain work-specific or sensitive files"
            exit 1
        fi
    done
done

# Check for sensitive content in files
SENSITIVE_CONTENT=(
    "OPEN[A]I_API"  # Split to avoid matching self
    "oai\.com"
    "api[_-]?key.*=.*['\"]"
    "secret.*=.*['\"]"
    "password.*=.*['\"]"
    "BEGIN.*PRIVATE KEY"
)

for file in $(git diff --cached --name-only); do
    # Skip checking hook setup scripts and documentation
    if [[ "$file" == *"setup-hooks.sh" ]] || [[ "$file" == *"pre-commit" ]] || [[ "$file" == *".md" ]]; then
        continue
    fi
    
    if [ -f "$file" ]; then
        for pattern in "${SENSITIVE_CONTENT[@]}"; do
            if grep -iE "$pattern" "$file" > /dev/null 2>&1; then
                echo "ERROR: File '$file' contains sensitive content matching pattern '$pattern'"
                echo "Please remove sensitive information before committing to common dotfiles"
                exit 1
            fi
        done
    fi
done

exit 0
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "Pre-commit hook installed successfully!"

git -C "$REPO_ROOT" config --local rebase.autostash false
git -C "$REPO_ROOT" config --local merge.autostash false
git -C "$REPO_ROOT" config --local alias.stash \
  '!echo "ERROR: git stash is disabled in this repo. Use a clean worktree instead." >&2; exit 1'
git -C "$REPO_ROOT" config --local alias.pull \
  '!f(){ for arg in "$@"; do if [ "$arg" = "--autostash" ]; then echo "ERROR: --autostash is disabled in this repo. Use a clean worktree instead." >&2; exit 1; fi; done; command git -c alias.pull= pull "$@"; }; f'
git -C "$REPO_ROOT" config --local alias.rebase \
  '!f(){ for arg in "$@"; do if [ "$arg" = "--autostash" ]; then echo "ERROR: --autostash is disabled in this repo. Use a clean worktree instead." >&2; exit 1; fi; done; command git -c alias.rebase= rebase "$@"; }; f'
git -C "$REPO_ROOT" config --local alias.merge \
  '!f(){ for arg in "$@"; do if [ "$arg" = "--autostash" ]; then echo "ERROR: --autostash is disabled in this repo. Use a clean worktree instead." >&2; exit 1; fi; done; command git -c alias.merge= merge "$@"; }; f'
echo "No-stash guardrails configured successfully!"
