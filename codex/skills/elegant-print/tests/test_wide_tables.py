import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader


SKILL_DIR = Path(__file__).resolve().parents[1]
TABLE_FILTER = SKILL_DIR / "scripts" / "wide_tables.lua"
DOCX_STYLE = SKILL_DIR / "scripts" / "docx_style.tex"
RENDERER = SKILL_DIR / "scripts" / "elegant_print.py"


def require_commands(*names: str) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        pytest.skip(f"missing required command(s): {', '.join(missing)}")


def filtered_document(html: str, environment: dict[str, str] | None = None) -> tuple[dict, str]:
    require_commands("pandoc")
    env = os.environ.copy()
    for name in (
        "ELEGANT_PRINT_LANDSCAPE_TABLES",
        "ELEGANT_PRINT_PORTRAIT_TABLES",
        "ELEGANT_PRINT_LANDSCAPE_THRESHOLD",
    ):
        env.pop(name, None)
    env.update(environment or {})

    result = subprocess.run(
        [
            "pandoc",
            "--from=html",
            "--to=json",
            f"--lua-filter={TABLE_FILTER}",
        ],
        input=html,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return json.loads(result.stdout), result.stderr


def only_table(document: dict) -> dict:
    tables = [block for block in document["blocks"] if block["t"] == "Table"]
    assert len(tables) == 1
    return tables[0]


def latex_raw_blocks(document: dict) -> list[str]:
    return [
        block["c"][1]
        for block in document["blocks"]
        if block["t"] == "RawBlock" and block["c"][0] == "latex"
    ]


def load_renderer():
    spec = importlib.util.spec_from_file_location("elegant_print_test_module", RENDERER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def table_rows(table: dict) -> list[list]:
    table_data = table["c"]
    rows = list(table_data[3][1])
    for body in table_data[4]:
        rows.extend(body[2])
        rows.extend(body[3])
    rows.extend(table_data[5][1])
    return rows


def test_narrow_table_stays_portrait() -> None:
    document, diagnostics = filtered_document(
        """
        <table>
          <thead><tr><th>Alpha</th><th>Beta</th><th>Gamma</th></tr></thead>
          <tbody><tr><td>NARROWONE</td><td>NARROWTWO</td><td>NARROWTHREE</td></tr></tbody>
        </table>
        """
    )

    table = only_table(document)
    raw_blocks = latex_raw_blocks(document)

    assert len(table["c"][2]) == 3
    assert "\\begin{landscape}" not in raw_blocks
    assert "\\end{landscape}" not in raw_blocks
    assert (
        "original_columns=3 columns=3 substantive=3 orientation=portrait "
        "removed_empty_columns=0 moved_header_rows=0"
    ) in diagnostics


def test_wide_table_uses_landscape() -> None:
    headers = "".join(f"<th>Header {index}</th>" for index in range(1, 7))
    cells = "".join(f"<td>WIDE{index}</td>" for index in range(1, 7))
    document, diagnostics = filtered_document(
        f"<table><thead><tr>{headers}</tr></thead><tbody><tr>{cells}</tr></tbody></table>"
    )

    table = only_table(document)
    raw_blocks = latex_raw_blocks(document)

    assert len(table["c"][2]) == 6
    assert raw_blocks.count("\\begin{landscape}") == 1
    assert raw_blocks.count("\\end{landscape}") == 1
    assert (
        "original_columns=6 columns=6 substantive=6 orientation=landscape "
        "removed_empty_columns=0 moved_header_rows=0"
    ) in diagnostics


def test_manual_portrait_override_wins_over_automatic_landscape() -> None:
    headers = "".join(f"<th>Header {index}</th>" for index in range(1, 7))
    cells = "".join(f"<td>OVERRIDE{index}</td>" for index in range(1, 7))
    document, diagnostics = filtered_document(
        f"<table><thead><tr>{headers}</tr></thead><tbody><tr>{cells}</tr></tbody></table>",
        {"ELEGANT_PRINT_PORTRAIT_TABLES": "1"},
    )

    assert "\\begin{landscape}" not in latex_raw_blocks(document)
    assert "substantive=6 orientation=portrait" in diagnostics


def test_fully_empty_columns_collapse_before_orientation() -> None:
    document, diagnostics = filtered_document(
        """
        <table>
          <thead>
            <tr><th>Alpha</th><th></th><th>Charlie</th><th>Delta</th><th></th><th>Foxtrot</th></tr>
          </thead>
          <tbody>
            <tr><td>A1</td><td></td><td>C1</td><td>D1</td><td></td><td>F1</td></tr>
            <tr><td>A2</td><td></td><td>C2</td><td>D2</td><td></td><td>F2</td></tr>
          </tbody>
        </table>
        """
    )

    table = only_table(document)
    raw_blocks = latex_raw_blocks(document)

    assert len(table["c"][2]) == 4
    assert all(len(row[1]) == 4 for row in table_rows(table))
    assert "\\begin{landscape}" not in raw_blocks
    assert (
        "original_columns=6 columns=4 substantive=4 orientation=portrait "
        "removed_empty_columns=2 moved_header_rows=0"
    ) in diagnostics


def test_colspan_and_rowspan_survive_filtering() -> None:
    document, diagnostics = filtered_document(
        """
        <table>
          <thead><tr><th colspan="2">Combined</th><th>Third</th><th>Fourth</th></tr></thead>
          <tbody>
            <tr><td rowspan="2">Shared</td><td>One</td><td>Two</td><td>Three</td></tr>
            <tr><td>Four</td><td>Five</td><td>Six</td></tr>
          </tbody>
        </table>
        """
    )

    table = only_table(document)
    cells = [cell for row in table_rows(table) for cell in row[1]]

    assert len(table["c"][2]) == 4
    assert any(cell[3] == 2 for cell in cells)
    assert any(cell[2] == 2 for cell in cells)
    assert "removed_empty_columns=0" in diagnostics
    assert "orientation=portrait" in diagnostics


def test_google_docs_repeating_header_rows_return_to_body(tmp_path: Path) -> None:
    require_commands("pandoc")
    docx = pytest.importorskip("docx")
    oxml = pytest.importorskip("docx.oxml")
    source = tmp_path / "all-repeating-headers.docx"
    document = docx.Document()
    table = document.add_table(rows=4, cols=3)
    for row_index, row in enumerate(table.rows):
        for column_index, cell in enumerate(row.cells):
            cell.text = f"R{row_index}C{column_index}"
        row._tr.get_or_add_trPr().append(oxml.OxmlElement("w:tblHeader"))
    document.save(source)

    result = subprocess.run(
        [
            "pandoc",
            str(source),
            "--from=docx",
            "--to=json",
            f"--lua-filter={TABLE_FILTER}",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    filtered = json.loads(result.stdout)
    filtered_table = only_table(filtered)

    assert len(filtered_table["c"][3][1]) == 1
    assert len(filtered_table["c"][4][0][3]) == 3
    assert "moved_header_rows=3" in result.stderr


def test_adjacent_wide_web_tables_share_one_full_width_landscape_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_commands("pandoc")
    renderer = load_renderer()
    headers = "".join(f"<th>Header {index}</th>" for index in range(1, 7))
    cells = "".join(f"<td>ADJACENT{index}</td>" for index in range(1, 7))
    table = f"<table><thead><tr>{headers}</tr></thead><tbody><tr>{cells}</tr></tbody></table>"
    html = (
        "<html><head><title>Adjacent Tables</title></head><body><main>"
        f"<p>Before</p>{table}{table}<p>After</p>"
        "</main></body></html>"
    )

    class Response:
        text = html

    monkeypatch.setattr(renderer.requests, "get", lambda *args, **kwargs: Response())
    tex, _ = renderer.build_web_tex(
        "https://example.test/tables",
        columns=2,
        paper="letter",
        outdir=tmp_path,
    )

    assert tex.count(r"\begin{landscape}") == 1
    assert tex.count(r"\end{landscape}") == 1
    assert "\\end{multicols}\n\\begin{landscape}" in tex
    assert "\\end{landscape}\n\n\\begin{multicols}{2}" in tex


def test_compiled_wide_table_page_is_rotated(tmp_path: Path) -> None:
    require_commands("pandoc", "latexmk", "xelatex")
    headers = "".join(f"<th>Column {index}</th>" for index in range(1, 7))
    cells = "".join(f"<td>LANDSCAPEMARKER{index}</td>" for index in range(1, 7))
    html = f"<table><thead><tr>{headers}</tr></thead><tbody><tr>{cells}</tr></tbody></table>"
    tex_path = tmp_path / "wide-table.tex"

    env = os.environ.copy()
    for name in (
        "ELEGANT_PRINT_LANDSCAPE_TABLES",
        "ELEGANT_PRINT_PORTRAIT_TABLES",
        "ELEGANT_PRINT_LANDSCAPE_THRESHOLD",
    ):
        env.pop(name, None)

    subprocess.run(
        [
            "pandoc",
            "--from=html",
            "--to=latex",
            "--standalone",
            "--pdf-engine=xelatex",
            f"--lua-filter={TABLE_FILTER}",
            f"--include-in-header={DOCX_STYLE}",
            "--metadata=title:Wide Table Test",
            "--variable=documentclass:article",
            "--variable=classoption:11pt,twoside",
            "--variable=geometry:letterpaper",
            f"--output={tex_path}",
        ],
        input=html,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    subprocess.run(
        [
            "latexmk",
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={tmp_path}",
            tex_path.name,
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )

    reader = PdfReader(str(tmp_path / "wide-table.pdf"))
    marker_pages = [
        page
        for page in reader.pages
        if "LANDSCAPEMARKER6" in (page.extract_text() or "")
    ]

    assert len(marker_pages) == 1
    assert int(marker_pages[0].get("/Rotate", 0)) % 180 == 90
