" Common Vim configuration
" Shared between work and personal environments

"------------------------------
" Basic settings
"------------------------------
set nocompatible              " Required by Vundle
filetype off                  " Required by Vundle before begin()

" Encoding
set encoding=utf-8
let mapleader=","

"------------------------------
" Local overrides (wrapper-friendly)
"------------------------------
" Source a single local override file early for variables/options/mappings
if filereadable(expand('~/.vimrc.local'))
  execute 'source' fnameescape(expand('~/.vimrc.local'))
endif
" Source all files in ~/.vimrc.d for modular overrides (sorted order)
for s:f in split(glob('~/.vimrc.d/*.vim'), "\n")
  if filereadable(s:f)
    execute 'source' fnameescape(s:f)
  endif
endfor

" Appearance
" Better natural word-wrap in text/Markdown files
augroup WordWrap
  autocmd!
  autocmd FileType markdown,text,plaintex setlocal wrap linebreak breakindent nolist
augroup END

" Visual bell instead of beep
set noerrorbells
set visualbell
set t_vb=

syntax on
set number
set relativenumber
set cursorline
set showcmd
set showmatch
set wildmenu
set lazyredraw
set ttyfast
set termguicolors            " If your terminal supports truecolour

" Robust 24-bit colour support for iTerm2 and modern terminals.
if !has('termguicolors')
  let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
  let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
endif

" Indentation
set tabstop=4
set shiftwidth=4
set expandtab
set autoindent
set smartindent

" Searching
set hlsearch
set incsearch
set ignorecase
set smartcase

" File handling
set hidden
set backup
set swapfile
set autoread

" Performance
set lazyredraw
set updatetime=250

" Mouse support
set mouse=a

" Display
set display+=lastline

" Status line
set laststatus=2
set ruler

" Command line
set showcmd
set cmdheight=1
set wildmenu
set wildmode=longest:full,full

" Persistent undo
if has('persistent_undo')
  silent !mkdir -p ~/.vim/undodir
  set undodir=~/.vim/undodir
  set undofile
endif

" Backup directories
silent !mkdir -p ~/.vim/backup
silent !mkdir -p ~/.vim/swap
set backupdir=~/.vim/backup//
set directory=~/.vim/swap//

"------------------------------
" Key mappings
"------------------------------
" Quick save
nnoremap <leader>w :w<CR>

" Clear search highlight
nnoremap <leader><space> :nohlsearch<CR>

" Move between splits
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l

" Buffer navigation
nnoremap <leader>bn :bnext<CR>
nnoremap <leader>bp :bprevious<CR>
nnoremap <leader>bd :bdelete<CR>

" Exit insert mode with ;;
inoremap ;; <Esc>

"------------------------------
" Plugin Configuration
"------------------------------
" Initialize Vundle
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

" Let Vundle manage Vundle (required)
Plugin 'VundleVim/Vundle.vim'

" Common plugins
Plugin 'preservim/nerdtree'
Plugin 'tpope/vim-fugitive'
Plugin 'tpope/vim-surround'
Plugin 'tpope/vim-commentary'
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'ctrlpvim/ctrlp.vim'
Plugin 'junegunn/goyo.vim'
Plugin 'junegunn/limelight.vim'
Plugin 'morhetz/gruvbox'

" Allow wrappers to add plugins without modifying common
if filereadable(expand('~/.vimrc.plugins'))
  execute 'source' fnameescape(expand('~/.vimrc.plugins'))
endif

call vundle#end()
filetype plugin indent on

"------------------------------
" Plugin settings
"------------------------------
" NERDTree
nnoremap <leader>n :NERDTreeToggle<CR>
let NERDTreeShowHidden=1
let NERDTreeIgnore=['\.pyc$', '\~$', '\.swp$', '\.DS_Store$']

" CtrlP
let g:ctrlp_map = '<c-p>'
let g:ctrlp_cmd = 'CtrlP'
let g:ctrlp_working_path_mode = 'ra'
let g:ctrlp_custom_ignore = '\v[\/]\.(git|hg|svn)$'

" Airline
let g:airline_powerline_fonts = 1
let g:airline#extensions#tabline#enabled = 1

" Goyo + Limelight integration
let g:limelight_paragraph_span = 1
let g:limelight_priority = -1

function! s:goyo_enter()
  if has('gui_running')
    set fullscreen
    set background=light
    set linespace=7
  elseif exists('$TMUX')
    silent !tmux set status off
  endif
  Limelight
  let &l:statusline = '%M'
  hi StatusLine ctermfg=red guifg=red cterm=NONE gui=NONE
endfunction

function! s:goyo_leave()
  if has('gui_running')
    set nofullscreen
    set background=dark
    set linespace=0
  elseif exists('$TMUX')
    silent !tmux set status on
  endif
  Limelight!
endfunction

autocmd! User GoyoEnter nested call <SID>goyo_enter()
autocmd! User GoyoLeave nested call <SID>goyo_leave()
nnoremap <silent> <leader>g :Goyo<CR>

"------------------------------
" File type specific settings
"------------------------------
augroup FileTypeSpecific
  autocmd!
  " Python
  autocmd FileType python setlocal shiftwidth=4 tabstop=4 expandtab
  " JavaScript/TypeScript
  autocmd FileType javascript,typescript,json setlocal shiftwidth=2 tabstop=2 expandtab
  " YAML
  autocmd FileType yaml setlocal shiftwidth=2 tabstop=2 expandtab
  " Markdown
  autocmd FileType markdown setlocal spell spelllang=en_us
  autocmd FileType markdown setlocal comments=b:*,b:-,b:+,n:> formatoptions=tcroqln
  autocmd FileType markdown setlocal formatlistpat=^\\s*\\d\\+\\.\\s\\+\\\\|^\\s*[-*+]\\s\\+
  " Tab/Shift-Tab for list indentation in markdown
  autocmd FileType markdown inoremap <buffer> <Tab> <C-t>
  autocmd FileType markdown inoremap <buffer> <S-Tab> <C-d>
  autocmd FileType markdown vnoremap <buffer> <Tab> >gv
  autocmd FileType markdown vnoremap <buffer> <S-Tab> <gv
augroup END

"------------------------------
" Color scheme
"------------------------------
" Set a default colorscheme that works in most terminals
" Wrappers can set g:preferred_colorscheme in ~/.vimrc.local
if exists('g:preferred_colorscheme')
  if has('termguicolors')
    set termguicolors
  endif
  try
    execute 'colorscheme ' . g:preferred_colorscheme
  catch
    if has('gui_running') || has('termguicolors')
      colorscheme gruvbox
      set background=dark
    else
      colorscheme default
    endif
  endtry
else
  if has('gui_running') || has('termguicolors')
    colorscheme gruvbox
    set background=dark
  else
    colorscheme default
  endif
endif