---
name: elegant-print
description: Create elegant, print-ready PDFs from articles, web pages, Google Docs exports, DOCX files, or CSVs using the original, quiet, Asterisk-inspired print layout, hanging footnotes, generous annotation margins, and tested wide-table handling.
---

# Elegant Print

## Preserve the original design

The output is the original Elegant Print design. Use 11 pt TeX Gyre Schola body text, TeX Gyre Heros headings, the original warm brown and blue, the compact centered title, indented paragraphs, mirrored annotation margins, ordinary inset quotations, and alternating outside page numbers.

Do not replace that design with a giant headline, a publication overline, conspicuous pull-quote rules, ornamental boxes, or a different font. The user prefers the original format. Improve hanging footnotes, source extraction, and table behavior without changing the overall look.

Treat a website as a source of article content, not a visual template. Preserve the source's substantive words, Unicode, links, images, captions, lists, heading structure, and genuine notes.

## Quick start

Resolve `scripts/elegant_print.py` relative to this skill when working in a checkout. On this laptop, use the installed path:

```bash
# Original-format article.
python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py \
  web "https://example.com/article" \
  --outfile ~/Downloads/example-article.pdf

# Original-format CSV.
python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py \
  csv ~/Downloads/data.csv \
  --outfile ~/Downloads/data-print.pdf

# Original-format Word document or exported Google Doc.
python /Users/dgr/.codex/skills/elegant-print/scripts/elegant_print.py \
  docx ~/Downloads/document.docx \
  --outfile ~/Downloads/document-print.pdf
```

Add `--open` only when the user asks to open the resulting PDF.

## Layout

- Use `--paper letter` by default or `--paper 7x10` when the user requests the smaller original trim.
- Use one prose column by default. Reserve `--columns 2` for reference material with few footnotes.
- Keep the original letter margins: `1.2 in` inside and `2.0 in` outside.
- Keep the original centered title, page-one treatment, paragraph indentation, colors, body and heading fonts, and outer-corner folios.
- Use ordinary upright, inset quotations. Do not add a colored line or pull-quote bar.
- Use hanging, flush-margin footnote labels and keep notes on the relevant page.

Use [Butterick's summary of key rules](https://practicaltypography.com/summary-of-key-rules.html), [block quotation guidance](https://practicaltypography.com/block-quotations.html), and [footnote guidance](https://typographyforlawyers.com/footnotes.html) as quality constraints. Do not trade away the user's preferred visual design to hit a particular measurement.

## Private Google Docs and wide tables

Export private Google Docs to DOCX through Google Drive, then use the `docx` command. Do not fetch a private Google Docs URL with `web`.

Preserve the tested Pandoc, XeLaTeX, and Lua wide-table behavior: automatic landscape orientation, substantive-column detection, safe empty-column removal, repaired repeating Google Docs headers, and return to portrait pages.

Repeat `--landscape-table N` or `--portrait-table N` to override a positive, one-based DOCX table number. Inspect the resulting headers, page transitions, rows, and continuation pages.

## Output and verification

- Put final PDFs directly in `~/Downloads` unless the user requests another destination.
- Honor the exact `--outfile`; do not create a final per-document directory.
- Preserve the requested article title and source figures and keep meaningful links clickable.
- Use `--outdir` only when intermediate TeX, downloaded assets, or diagnostics are requested.
- Use the original LaTeX renderer for articles and CSVs and the existing Pandoc and XeLaTeX renderer for DOCX.
- Report a missing required tool directly; do not silently substitute a visually different renderer.
- Inspect the first and a representative reading page, checking that the output actually resembles the original Elegant Print format.
- Run the classic article, CSV, hanging-footnote, and wide-table tests before delivery.

## Resources

- `scripts/elegant_print.py`: original-format article, CSV, and DOCX rendering.
- `scripts/docx_style.tex`: original Schola/Heros Word and Google Docs styling.
- `scripts/wide_tables.lua`: tested table normalization and landscape orientation.
- `references/style.md`: the original, user-preferred visual design.
- `tests/`: original-format output, complete CSV records, hanging notes, and wide-table regression tests.
