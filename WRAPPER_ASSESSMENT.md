# Wrapper Assessment Guide

This guide helps work-side agents periodically assess what customizations in wrapper repositories may no longer be needed due to improvements in the common submodule.

## Assessment Process

### 1. Review Extension Points

The common configuration now provides these extension points that may eliminate the need for wrapper overrides:

#### Vim Configuration
- **`~/.vimrc.local`**: Early-loaded settings, variables, and mappings
- **`~/.vimrc.d/*.vim`**: Modular configuration files (loaded in sorted order)
- **`~/.vimrc.plugins`**: Additional plugins (format: `Plugin 'owner/repo'`)
- **`g:preferred_colorscheme`**: Set in `~/.vimrc.local` to override default theme

#### Zsh Configuration  
- **`~/.zshrc.local`**: Environment-specific settings

#### Git Configuration
- **`~/.gitconfig.local`**: User-specific configuration

### 2. Migration Opportunities

Review your wrapper repository for these patterns that can now use extension points:

#### Direct File Modifications
- **Before**: Modified `common/vim/.vimrc` directly
- **After**: Move customizations to `~/.vimrc.local` or `~/.vimrc.d/`

#### Plugin Additions
- **Before**: Added plugins directly to common's .vimrc
- **After**: List additional plugins in `~/.vimrc.plugins`

#### Theme/Colorscheme Overrides
- **Before**: Modified colorscheme section in common's .vimrc  
- **After**: Set `let g:preferred_colorscheme = 'theme-name'` in `~/.vimrc.local`

#### Complex Overrides
- **Before**: Copied entire common file with modifications
- **After**: Symlink to common file + use extension points

### 3. Assessment Questions

When reviewing your wrapper repository, ask:

1. **Is this override still necessary?**
   - Does common now provide an extension point for this customization?
   - Has the default behavior in common changed to meet your needs?

2. **Can this be simplified?**
   - Can a full file replacement become a small extension file?
   - Can hardcoded values use the new variable-based approach?

3. **Is this work-specific?**
   - Does this truly need to be different from personal environment?
   - Could this customization benefit the common configuration?

### 4. Migration Checklist

For each file in your wrapper repository:

- [ ] **Vim**: Check if overrides can move to extension points
- [ ] **Zsh**: Verify only work-specific items remain in local overrides  
- [ ] **Git**: Confirm only work-specific config (email, signing) in local
- [ ] **New configs**: Consider if new tool configs should start in common

### 5. Testing Migration

When migrating overrides to extension points:

1. **Backup**: Keep current wrapper config as backup
2. **Incremental**: Migrate one customization at a time
3. **Test**: Verify behavior matches previous setup
4. **Clean**: Remove unnecessary wrapper files

### 6. Ongoing Assessment

Perform this assessment:
- **After common updates**: Check if new extension points eliminate wrapper needs
- **Quarterly**: Review wrapper complexity and migration opportunities  
- **Before new customizations**: Check if extension points can handle new needs

## Extension Point Examples

### Vim Theme Override
```vim
" In ~/.vimrc.local
let g:preferred_colorscheme = 'solarized'
```

### Vim Work-Specific Mappings
```vim
" In ~/.vimrc.d/01-work.vim
" Work-specific key mappings
nnoremap <leader>jira :!open https://company.atlassian.net<CR>
```

### Additional Vim Plugins
```vim
" In ~/.vimrc.plugins
Plugin 'company/internal-vim-plugin'
Plugin 'fatih/vim-go'
```

This assessment should help identify opportunities to simplify wrapper repositories while taking advantage of the improved extension points in common.