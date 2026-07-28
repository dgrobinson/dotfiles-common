import importlib.util
import shutil
import sys
import unicodedata
from pathlib import Path

import pytest
from pypdf import PdfReader


SKILL_DIR = Path(__file__).resolve().parents[1]
RENDERER = SKILL_DIR / "scripts" / "elegant_print.py"
ARTICLE_URL = "https://example.test/classic-article"
ARTICLE_TITLE = "The Quiet Classic Article — Café"
ARTICLE_HTML = f"""
<!doctype html>
<html lang="en">
  <head>
    <title>{ARTICLE_TITLE}</title>
    <meta property="og:title" content="{ARTICLE_TITLE}">
  </head>
  <body>
    <nav><h1>An Unrelated Site Masthead</h1></nav>
    <article>
      <h1>{ARTICLE_TITLE}</h1>
      <p>
        CLASSICOPENINGMARKER preserves naïve prose and
        <a href="https://example.test/classic-evidence">primary evidence</a>.
      </p>
      <blockquote>
        <p>CLASSICQUOTEMARKER remains an ordinary, quiet inset quotation.</p>
      </blockquote>
      <p>CLASSICENDINGMARKER preserves the genuine source ending.</p>
    </article>
  </body>
</html>
"""


@pytest.fixture
def renderer():
    spec = importlib.util.spec_from_file_location(
        "elegant_print_classic_test_module",
        RENDERER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def comparison_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def test_original_preamble_preserves_font_margin_and_hanging_notes(renderer) -> None:
    preamble, _ = renderer.latex_preamble(
        title="A quiet original title",
        subtitle="A real source",
        footer="Source: example.test",
        columns=1,
        paper="letter",
    )

    assert r"\documentclass[11pt,letterpaper,twoside]{article}" in preamble
    assert r"\usepackage{tgschola}" in preamble
    assert r"\usepackage{tgheros}" in preamble
    assert r"\usepackage[bottom,hang,flushmargin]{footmisc}" in preamble
    assert "inner=1.2in,outer=2.0in" in preamble
    assert r"\definecolor{Accent}{HTML}{7A3B2E}" in preamble
    assert r"\LARGE\scshape" in preamble
    assert r"\setlength{\parindent}{1.1em}" in preamble
    assert r"\setlength{\parskip}{0pt}" in preamble


def test_compact_paper_keeps_original_classic_margins(renderer) -> None:
    preamble, _ = renderer.latex_preamble(
        title="A quiet original title",
        subtitle="A real source",
        footer="Source: example.test",
        columns=1,
        paper="7x10",
    )

    assert "paperwidth=7in,paperheight=10in" in preamble
    assert "inner=1.0in,outer=1.6in" in preamble
    assert r"\usepackage{tgschola}" in preamble
    assert r"\usepackage[bottom,hang,flushmargin]{footmisc}" in preamble


def test_csv_uses_source_filename_instead_of_hardcoded_dataset(
    renderer,
    tmp_path: Path,
) -> None:
    source = tmp_path / "my genuine source.csv"
    source.write_text("Title\nA real record\n", encoding="utf-8")

    tex = renderer.build_csv_tex(source, columns=1, paper="letter")

    assert "pdftitle={my genuine source}" in tex
    assert "my genuine source.csv" in tex
    assert "CSLAW 2026 Data" not in tex
    assert r"\usepackage{tgschola}" in tex


def test_csv_keeps_all_standard_and_unexpected_source_fields(
    renderer,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source records.csv"
    source.write_text(
        "ID,Title,Authors,Abstract,Additional context,Final source field\n"
        'ROW-01,"Über reference entry",A Real Author,'
        '"ABSTRACTMARKER retains the original abstract",'
        '"EXTRAMARKER retains an unexpected column",'
        '"FINALMARKER retains the final source field"\n',
        encoding="utf-8",
    )

    tex = renderer.build_csv_tex(source, columns=1, paper="letter")

    for value in (
        "ROW-01",
        "Über reference entry",
        "A Real Author",
        "ABSTRACTMARKER",
        "Additional context:",
        "EXTRAMARKER",
        "Final source field:",
        "FINALMARKER",
    ):
        assert value in tex


def test_csv_ignores_empty_rows_without_losing_real_source_fields(
    renderer,
    tmp_path: Path,
) -> None:
    source = tmp_path / "sparse source.csv"
    source.write_text(
        "Title,Additional context\n"
        ",\n"
        '"A substantive record","SPARSEMARKER remains visible"\n'
        ",\n",
        encoding="utf-8",
    )

    tex = renderer.build_csv_tex(source, columns=1, paper="letter")

    assert tex.count("A substantive record") == 1
    assert "Additional context:" in tex
    assert "SPARSEMARKER remains visible" in tex


@pytest.mark.skipif(shutil.which("tectonic") is None, reason="Tectonic is required")
def test_article_renders_the_original_format_without_quote_bars(
    renderer,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class ArticleResponse:
        text = ARTICLE_HTML

    monkeypatch.setattr(
        renderer.requests,
        "get",
        lambda url, **kwargs: ArticleResponse(),
    )
    calls: list[list[str]] = []
    original_run = renderer.subprocess.run

    def record_run(command, *args, **kwargs):
        calls.append(list(command))
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(renderer.subprocess, "run", record_run)
    outdir = tmp_path / "classic-article-intermediates"
    output = tmp_path / "classic article.pdf"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RENDERER),
            "web",
            ARTICLE_URL,
            "--outdir",
            str(outdir),
            "--outfile",
            str(output),
        ],
    )

    renderer.main()

    tex = (outdir / "elegant-print.tex").read_text(encoding="utf-8")
    assert r"\documentclass[11pt,letterpaper,twoside]{article}" in tex
    assert r"\usepackage{tgschola}" in tex
    assert r"\usepackage{tgheros}" in tex
    assert r"\usepackage[bottom,hang,flushmargin]{footmisc}" in tex
    assert r"\definecolor{Accent}{HTML}{7A3B2E}" in tex
    assert r"\LARGE\scshape" in tex
    assert r"\begin{quote}" in tex
    assert "left: 1.55pt + accent" not in tex
    assert [command[0] for command in calls] == ["tectonic"]

    rendered = pdf_text(output)
    assert "CLASSICOPENINGMARKER" in rendered
    assert "CLASSICQUOTEMARKER" in rendered
    assert "CLASSICENDINGMARKER" in rendered
    assert PdfReader(str(output)).metadata.title == ARTICLE_TITLE


@pytest.mark.skipif(shutil.which("tectonic") is None, reason="Tectonic is required")
def test_csv_renders_every_source_field_in_original_format(
    renderer,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "unexpected source records.csv"
    source.write_text(
        "ID,Title,Authors,Abstract,Additional context,Another source field\n"
        'ROW-01,"Über reference entry",An Original Author,'
        '"CLASSICABSTRACTMARKER retains the original abstract",'
        '"CLASSICEXTRAMARKER preserves an unexpected column",'
        '"CLASSICFINALMARKER preserves the final source field"\n',
        encoding="utf-8",
    )
    calls: list[list[str]] = []
    original_run = renderer.subprocess.run

    def record_run(command, *args, **kwargs):
        calls.append(list(command))
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(renderer.subprocess, "run", record_run)
    outdir = tmp_path / "classic-csv-intermediates"
    output = tmp_path / "classic records.pdf"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RENDERER),
            "csv",
            str(source),
            "--outdir",
            str(outdir),
            "--outfile",
            str(output),
        ],
    )

    renderer.main()

    tex = (outdir / "elegant-print.tex").read_text(encoding="utf-8")
    assert r"\usepackage{tgschola}" in tex
    assert r"\usepackage{tgheros}" in tex
    assert r"\usepackage[bottom,hang,flushmargin]{footmisc}" in tex
    assert "Über reference entry" in tex
    assert "Additional context:" in tex
    assert "Another source field:" in tex
    assert [command[0] for command in calls] == ["tectonic"]

    rendered = comparison_text(pdf_text(output))
    for marker in (
        "ROW-01",
        "CLASSICABSTRACTMARKER",
        "CLASSICEXTRAMARKER",
        "CLASSICFINALMARKER",
    ):
        assert comparison_text(marker) in rendered
    assert PdfReader(str(output)).metadata.title == source.stem
