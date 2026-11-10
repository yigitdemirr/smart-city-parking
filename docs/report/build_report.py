"""Build the M1 report (DOCX + PDF) and the Markdown scenario matrix.

Usage (from the repository root):
    python3 docs/report/build_report.py
Needs: pandoc, LibreOffice (soffice), python-docx.
"""
import csv
import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "docs" / "report"
CSV_PATH = ROOT / "docs" / "network-scenarios.csv"

TRACE = [
    ("F1", "UC1", "POST /auth/register", "users", "NS-01, NS-02"),
    ("F2", "UC2", "POST /auth/login", "users", "NS-03"),
    ("F3", "UC3", "client location module (observedAt, accuracyM)", "–", "NS-05, NS-06"),
    ("F4", "UC3", "GET /facilities/nearby", "parking_facilities, parking_spaces, reservations", "NS-04 – NS-07"),
    ("F5", "UC4", "GET /facilities/{id}/spaces", "parking_spaces, reservations", "NS-08"),
    ("F6", "UC5", "POST /reservations", "reservations, operations", "NS-09 – NS-14"),
    ("F7", "UC6", "POST /reservations/{id}/payment", "payments, reservations, operations", "NS-15 – NS-18"),
    ("F8", "UC7", "POST /reservations/{id}/cancel", "reservations, operations", "NS-19, NS-20"),
    ("F9", "UC8", "GET /reservations, GET /reservations/{id}", "reservations", "NS-21, NS-22"),
    ("F10", "UC9", "GET /operations/{operationId}", "operations", "NS-10, NS-11, NS-15, NS-26"),
    ("F11", "UC10", "POST /admin/facilities, POST /admin/facilities/{id}/spaces, PATCH /admin/spaces/{id}",
     "parking_facilities, parking_spaces, operations", "NS-24, NS-25"),
    ("F12", "UC11", "expiry job (service-internal)", "reservations", "NS-16, NS-20, NS-23"),
    ("F13", "all", "client (cache, pending store)", "local SQLite cache", "NS-04, NS-09, NS-18, NS-21, NS-22, NS-26"),
]


def esc(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def scenario_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def scenario_table_for_report(rows) -> str:
    out = ["| ID | Function – scenario | Situation | User-visible state | Server state | Expected result (test) |",
           "|----|--------------|----------------|------------------|--------------|----------------------|"]
    for r in rows:
        out.append("| " + " | ".join(esc(x) for x in [
            r["ID"], f'**{r["Function"]}** – {r["Scenario"]}', r["Situation"],
            r["User-visible state"], r["Server state"], r["Expected result (testable)"]]) + " |")
    return "\n".join(out)


def trace_table() -> str:
    out = ["| Requirement | Use case | API / component | Tables | Scenarios |",
           "|------|------|--------------------|------------------|--------------|"]
    for row in TRACE:
        out.append("| " + " | ".join(esc(x) for x in row) + " |")
    return "\n".join(out)


def check_consistency(rows):
    """Every scenario is traced to a requirement, every API path exists in openapi.yaml."""
    ids = {r["ID"] for r in rows}
    traced = set()
    for *_, scen in TRACE:
        for part in scen.split(","):
            part = part.strip()
            m = re.match(r"NS-(\d+)\s*–\s*NS-(\d+)", part)
            if m:
                traced |= {f"NS-{i:02d}" for i in range(int(m[1]), int(m[2]) + 1)}
            elif part.startswith("NS-"):
                traced.add(part)
    missing = sorted(ids - traced)
    assert not missing, f"scenarios not traced to any requirement: {missing}"
    spec = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
    spec_paths = set(re.findall(r"^  (/[^:]+):", spec, flags=re.M))
    for *_, api, _, _ in TRACE:
        for p in re.findall(r"(?:GET|POST|PATCH) (/[^\s,]+)", api):
            norm = re.sub(r"\{[^}]+\}", "{}", p)
            assert any(re.sub(r"\{[^}]+\}", "{}", s) == norm for s in spec_paths), f"{p} missing in openapi.yaml"
    print(f"consistency OK: {len(ids)} scenarios traced, API paths match openapi.yaml")


def write_scenarios_md(rows):
    lines = ["# Requirements and network-scenario matrix (Project B)", "",
             "Source of truth: `network-scenarios.csv`. Each row is a test case for M3.", "",
             "| " + " | ".join(rows[0].keys()) + " |", "|" + "---|" * len(rows[0])]
    for r in rows:
        lines.append("| " + " | ".join(esc(v) for v in r.values()) + " |")
    (ROOT / "docs" / "network-scenarios.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- DOCX styling
TEMPLATE = ROOT / "docs" / "report" / "Project_Documentation_Template_EN.docx"


def make_reference_docx(path: Path):
    """Use the course template as the style source (fonts, heading colours, page size).
    The template lacks the styles pandoc needs for tables, code and figures
    (Table, Compact, Source Code, Image Caption ...); copy only those from
    pandoc's default reference document, leaving the template's own styles intact."""
    import io
    import zipfile
    from lxml import etree
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    default = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                             capture_output=True, check=True).stdout
    def_styles = etree.fromstring(zipfile.ZipFile(io.BytesIO(default)).read("word/styles.xml"))
    tpl = zipfile.ZipFile(TEMPLATE)
    tpl_styles = etree.fromstring(tpl.read("word/styles.xml"))
    have = {st.get(W + "styleId") for st in tpl_styles.iter(W + "style")}
    for st in def_styles.iter(W + "style"):
        if st.get(W + "styleId") not in have:
            tpl_styles.append(st)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in tpl.infolist():
            data = tpl.read(item.filename)
            if item.filename == "word/styles.xml":
                data = etree.tostring(tpl_styles, xml_declaration=True, encoding="UTF-8", standalone=True)
            z.writestr(item, data)
    path.write_bytes(out.getvalue())
    doc = Document(path)
    by_name = {st.name: st for st in doc.styles}
    for name in ("Source Code", "Verbatim Char"):
        if name in by_name:
            by_name[name].font.size = Pt(7.5)
    doc.save(path)


def set_cell_shading(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "9AA5B1")
        borders.append(el)
    tbl_pr.append(borders)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


TEXT_WIDTH_TWIPS = 9638


def set_column_widths(table, is_meta, font_pt):
    """Spread the table over the full text width (17 cm), proportional to content,
    but never narrower than the longest single word of a column."""
    total_twips = TEXT_WIDTH_TWIPS
    ncols = len(table.columns)
    if is_meta:
        widths = [int(total_twips * 0.27), int(total_twips * 0.73)]
    else:
        weights, mins = [], []
        for j in range(ncols):
            texts = [row.cells[j].text for row in table.rows]
            lens = [len(t) for t in texts]
            mean = sum(lens) / len(lens)
            weights.append(max(min(max(lens), 45) * 0.35 + mean * 0.65, 3))
            longest = max((len(w) for t in texts for w in t.split()), default=3)
            longest = min(longest, 22)
            mins.append(int(longest * font_pt * 0.56 * 20 + 260))
        widths = [total_twips * w / sum(weights) for w in weights]
        for _ in range(5):  # enforce minimums, shrink the flexible columns
            fixed = [j for j in range(ncols) if widths[j] <= mins[j]]
            for j in fixed:
                widths[j] = mins[j]
            free = [j for j in range(ncols) if j not in fixed]
            rest = total_twips - sum(widths[j] for j in fixed)
            wsum = sum(weights[j] for j in free) or 1
            for j in free:
                widths[j] = rest * weights[j] / wsum
        widths = [int(w) for w in widths]
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    for tag in ("w:tblW", "w:tblLayout"):
        for el in tbl_pr.findall(qn(tag)):
            tbl_pr.remove(el)
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(total_twips))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_pr.append(tbl_w)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    grid = tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    for row in table.rows:
        for cell, w in zip(row.cells, widths):
            tc_pr = cell._tc.get_or_add_tcPr()
            for el in tc_pr.findall(qn("w:tcW")):
                tc_pr.remove(el)
            tc_w = OxmlElement("w:tcW")
            tc_w.set(qn("w:w"), str(w))
            tc_w.set(qn("w:type"), "dxa")
            tc_pr.insert(0, tc_w)


def postprocess(docx_path: Path):
    global TEXT_WIDTH_TWIPS
    doc = Document(docx_path)
    sec = doc.sections[0]
    TEXT_WIDTH_TWIPS = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)
    for i, table in enumerate(doc.tables):
        ncols = len(table.columns)
        size = Pt(7.5) if ncols >= 6 else Pt(8.5) if ncols >= 4 else Pt(9.5)
        set_column_widths(table, False, size.pt)
        set_table_borders(table)
        is_meta = False
        for r_idx, row in enumerate(table.rows):
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(1)
                    p.paragraph_format.space_before = Pt(1)
                    for run in p.runs:
                        run.font.size = Pt(10.5) if is_meta else size
            if r_idx == 0 and not is_meta:
                repeat_header(row)
                for cell in row.cells:
                    set_cell_shading(cell, "DCE6F2")
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.bold = True
    # captions centred, page break before the first chapter
    for p in doc.paragraphs:
        if p.style.name in ("Image Caption", "Captioned Figure"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p.style.name.startswith("Heading") and (p.text.startswith("3.5.") or p.text.startswith("Appendix A")):
            p.paragraph_format.page_break_before = True
    doc.save(docx_path)


def main():
    rows = scenario_rows()
    check_consistency(rows)
    write_scenarios_md(rows)

    src = (REPORT_DIR / "M1_report.md").read_text(encoding="utf-8")
    src = src.replace("{{SCENARIO_TABLE}}", scenario_table_for_report(rows))
    src = src.replace("{{TRACE_TABLE}}", trace_table())
    import os
    commit = os.environ.get("M1_COMMIT", "")
    src = src.replace("{{COMMIT}}", f" (commit `{commit}`)" if commit else "")
    build_md = REPORT_DIR / "_build.md"
    build_md.write_text(src, encoding="utf-8")

    ref = REPORT_DIR / "_reference.docx"
    make_reference_docx(ref)
    out_docx = REPORT_DIR / "M1_Report_Project_B.docx"
    subprocess.run(["pandoc", str(build_md), "-o", str(out_docx), "--reference-doc", str(ref),
                    "--resource-path", str(REPORT_DIR), "--columns", "200"], check=True)
    postprocess(out_docx)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(REPORT_DIR), str(out_docx)],
                   check=True, capture_output=True)
    build_md.unlink()
    ref.unlink()
    print("built", out_docx, out_docx.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
