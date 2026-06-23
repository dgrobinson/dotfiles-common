---
name: elegant-print
description: Create elegant, print-ready PDFs from web pages, Google Docs exports, DOCX files, or CSV files with Butterick-friendly line lengths, alternating outer page numbers, Asterisk-inspired typography, and automatic landscape handling for wide tables. Use when the user asks to convert a URL/article, document, or CSV into a beautiful PDF for printing, reading, or annotation, and when footnotes should stay near the text. Also use when the user wants single- or two-column print layouts.
---

# Elegant Print

## Overview
Generate print-ready PDFs from web pages, DOCX documents, or CSV data using a consistent, Asterisk-inspired layout with note-friendly margins, alternating outer page numbers, optional two-column layouts, and mixed portrait/landscape pages for table-heavy documents.

## Quick Start

Resolve `scripts/elegant_print.py` relative to this `SKILL.md` when working from a checkout or worktree. The commands below use the normal installed-skill path.

- **Web page → PDF**
  ```bash
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py web "https://example.com" --outfile ~/Downloads/example-article.pdf --open
  ```

- **CSV → PDF**
  ```bash
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py csv ~/Downloads/file.csv --outfile ~/Downloads/file-print.pdf --open
  ```

- **DOCX or Google Docs export → PDF**
  ```bash
  python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py docx ~/Downloads/document.docx --outfile ~/Downloads/document-print.pdf --open
  ```

## Private Google Docs

- Prefer a Google Drive export/download to DOCX. If Drive tooling is unavailable, use the authenticated browser's **File → Download → Microsoft Word (.docx)** action.
- Render the local export with the `docx` command. Do not pass a private Google Docs URL to `web`; an unauthenticated fetch cannot reliably recover the document or its tables.
- The DOCX renderer repairs the Google Docs export pattern that incorrectly marks every row in some tables as a repeating header.

## Laptop Output Default

- When running on DGR's laptop, put final PDFs directly in the root of `~/Downloads` with descriptive filenames unless the user explicitly gives another destination.
- Do not put final PDFs in per-document folders by default. Use `--outfile ~/Downloads/<descriptive-name>.pdf` when the desired filename is known.
- If no `--outdir` or `--outfile` is provided, the script compiles in a temporary directory and writes `~/Downloads/<title>.pdf`.
- Use `--outdir` only when the user needs the generated `.tex`, asset files, or other intermediates preserved.

## Core Workflow

1) **Pick input type**
   - URL/article → `web`
   - Local DOCX or private Google Docs export → `docx`
   - CSV file → `csv`

2) **Choose layout options**
   - For web and CSV, `--columns 1` (default) is best for footnote-heavy or long-form reading.
   - For web and CSV, `--columns 2` is useful for compact reference-style reading with fewer footnotes.
   - `--paper letter` (default) or `--paper 7x10` for a tighter, magazine-like trim.
   - For DOCX only, repeat `--landscape-table N` or `--portrait-table N` to override the automatic orientation of 1-based table `N`.

3) **Render + open**
   - Use `--open` to launch in Preview right after build.

4) **Verify table-heavy output**
   - Read the per-table stderr lines for the original column count, substantive column count, selected orientation, removed empty columns, and repaired header rows.
   - Open the final PDF and check every mixed-orientation transition, table header, row break, and outer page number before delivery.
   - If the automatic choice is wrong for a DOCX table, rerender with a manual orientation override. Use `--outdir` when compiler logs and generated TeX are needed for diagnosis.

Table-rich web and DOCX rendering requires Pandoc, `latexmk`, and XeLaTeX. The script reports a direct dependency error if one is unavailable.

## Wide Tables

- Web and DOCX tables with more than four **substantive** columns automatically render on landscape pages. Columns that are empty in every row do not count toward the threshold.
- Fully empty columns are removed only when every row has a simple one-cell-per-column shape. If any row uses `rowspan` or `colspan`, the table is left structurally unchanged.
- Web tables may opt in or out with a `landscape` or `portrait` class. DOCX tables use the 1-based `--landscape-table N` and `--portrait-table N` overrides.
- Adjacent wide tables may share one landscape run so short comparison tables do not each force a mostly empty page.
- In web `--columns 2` mode, tables temporarily leave the two-column text flow and render at full page width.

## Outputs

- By default on this laptop, the script writes the final PDF to the root of `~/Downloads` using the document title or CSV name.
- If `--outfile` is provided, the final PDF is written to that exact path.
- If `--outdir` is provided, the script also preserves `elegant-print.tex`, assets, and intermediate files there.
- For web pages, the PDF title uses the article/post title (usually the page `<h1>`).
- For DOCX files, the PDF title uses document metadata when available and otherwise falls back to the filename.
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
- `elegant_print.py`: main renderer for web, DOCX, and CSV inputs, with layout and manual table-orientation options.
- `wide_tables.lua`: Pandoc table normalization, substantive-column counting, and mixed-orientation handling.
- `docx_style.tex`: Elegant Print typography and table styling for Pandoc DOCX conversion.

### references/
- `style.md`: layout defaults and typography notes.
