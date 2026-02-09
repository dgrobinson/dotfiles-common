# Push From Work Environment

Use this when `git push` behavior differs between personal and work environments.

## Common Submodule (`dgrobinson/dotfiles-common`)

1) Standard path:
```bash
git -C common push origin main
```

2) If rejected because remote moved:
```bash
git -C common fetch origin main
git -C common rebase origin/main
git -C common push origin main
```

3) If HTTPS push fails or stalls (for example transient GitHub 500):
```bash
git -C common push git@github.com:dgrobinson/dotfiles-common.git main
```

4) Refresh tracking ref after SSH fallback:
```bash
git -C common fetch git@github.com:dgrobinson/dotfiles-common.git main:refs/remotes/origin/main
```

## Wrapper Repo (`openai/dgr-dotfiles`)

This repo may require SAML-authorized credentials in work environments.

Preferred push command:
```bash
git -c credential.helper='!gh auth git-credential' push origin main
```

Prereq check:
```bash
gh auth status -h github.com
```

If SSH push fails with org SAML enforcement, continue using HTTPS token-based auth.

## Safety

- Push `common` first, then commit/push wrapper submodule pointer.
- Do not use `git stash` or `--autostash` in this repo.
- Keep unrelated local modifications unstaged.
