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
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py web "https://example.com" --outfile ~/Downloads/example-article.pdf --open
  ```

- **CSV → PDF**
  ```bash
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py csv ~/Downloads/file.csv --outfile ~/Downloads/file-print.pdf --open
  ```

## Laptop Output Default

- When running on DGR's laptop, put final PDFs directly in the root of `~/Downloads` with descriptive filenames unless the user explicitly gives another destination.
- Do not put final PDFs in per-document folders by default. Use `--outfile ~/Downloads/<descriptive-name>.pdf` when the desired filename is known.
- If no `--outdir` or `--outfile` is provided, the script compiles in a temporary directory and writes `~/Downloads/<title>.pdf`.
- Use `--outdir` only when the user needs the generated `.tex`, asset files, or other intermediates preserved.

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

- By default on this laptop, the script writes the final PDF to the root of `~/Downloads` using the document title or CSV name.
- If `--outfile` is provided, the final PDF is written to that exact path.
- If `--outdir` is provided, the script also preserves `elegant-print.tex`, assets, and intermediate files there.
- For web pages, the PDF title uses the article/post title (usually the page `<h1>`).
- When available, the web page publish date is shown in the title block (for example: `Published February 9, 2026`).
- Front matter is compact: no dedicated cover page.
- A table of contents is included only when the rendered content is at least 10 pages, measured from a no-ToC compile.
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
