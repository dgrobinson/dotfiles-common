---
name: elegant-print
description: Create elegant, print-ready PDFs from web pages or CSV files with Butterick-friendly line lengths, alternating outer page numbers, and Asterisk-inspired typography. Use when the user asks to convert a URL/article or CSV into a beautiful PDF for printing, reading, or annotation, and when footnotes should stay near the text. Also use when the user wants single- or two-column print layouts.
---

# Elegant Print

## Overview
Generate print-ready PDFs from web pages or CSV data using a consistent, Asterisk-inspired layout with note-friendly margins, alternating outer page numbers, and optional two-column layouts.

## Quick Start

- **Web page → PDF**
  ```bash
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py web "https://example.com" --outdir /Users/dgr/code/tmp/print --open
  ```

- **CSV → PDF**
  ```bash
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py csv ~/Downloads/file.csv --outdir /Users/dgr/code/tmp/print --open
  ```

## Core Workflow

1) **Pick input type**
   - URL/article → `web`
   - CSV file → `csv`

2) **Choose layout options**
   - `--columns 1` (default): best for footnote-heavy or long-form reading.
   - `--columns 2`: use for compact reference-style reading with fewer footnotes.
   - `--paper letter` (default) or `--paper 7x10` for a tighter, magazine-like trim.

3) **Render + open**
   - Use `--open` to launch in Preview right after build.

## Outputs

- The script writes `elegant-print.tex` and `elegant-print.pdf` into the provided `--outdir`.
- For web pages, the PDF title uses the article/post title (usually the page `<h1>`).
- When available, the web page publish date is shown in the title block (for example: `Published February 9, 2026`).
- Front matter is compact: no dedicated cover page; title + ToC start on page 1.
- Web renders include inline content images (decorative tiny avatars/icons are skipped).
- Links are clickable in the PDF and styled in a distinct color with a subtle external-link icon (arrow out of a box); raw URLs are not printed inline.
- Page numbers are **alternating outer corners** with the “/ total” in light gray.
- Margins are tuned for **handwritten notes** in the outer margin.

## Notes on Footnotes

- **Web pages**: the script converts common footnote patterns (Wikipedia refs, simple numbered footnotes, and Substack-style endnotes) into LaTeX footnotes so they appear on the same page.
- **Two-column mode**: LaTeX footnotes in multicolumn layout can be less stable; prefer one column for heavy citation density.

## Style Adjustments (Asterisk‑Inspired Feel)

If the output needs to feel more like the Asterisk PDF sample:
- Use `--paper 7x10` for trim proportion.
- Keep `--columns 1` unless the source is short.
- Adjust warm accent color or margins inside `scripts/elegant_print.py` (see `latex_preamble`).

Refer to `references/style.md` for defaults.

## Resources

### scripts/
- `elegant_print.py`: main renderer for web + CSV inputs, with layout options.

### references/
- `style.md`: layout defaults and typography notes.
