"""Build the Word version of the report from report/report.html.

Layout mirrors the PDF: A4, two columns, 10 pt Times New Roman, ICML-like tables.
"""
from pathlib import Path
import re

from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
DOCX_OUT = REPORT / "report.docx"
COL_W = Cm(8.45)
BODY = 10
GRAY = RGBColor(0x8B, 0x97, 0xA8)

# figures that were re-plotted at column width for this version
DOCX_FIGS = {
    "fig4_by_gender.png": REPORT / "docx_assets" / "fig4_docx.png",
    "fig5_k_selection.png": REPORT / "docx_assets" / "fig5_docx.png",
}


# ----------------------------------------------------------------- helpers
def set_run_font(run, size=BODY, bold=None, italic=None, color=None, mono=False):
    name = "Consolas" if mono else "Times New Roman"
    run.font.name = name
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), "SimSun")


def clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def add_inline(par, node, size=BODY, bold=False, italic=False, color=None):
    """Copy inline markup (b / i / span / sup / code / br) into a paragraph."""
    for child in node.children:
        if isinstance(child, NavigableString):
            text = clean(str(child))
            if not text:
                continue
            run = par.add_run((" " if par.runs and not par.runs[-1].text.endswith(" ") else "") + text)
            set_run_font(run, size, bold, italic, color)
        elif isinstance(child, Tag):
            name = child.name
            style = child.get("style", "")
            if name == "br":
                par.add_run().add_break()
            elif name in ("b", "strong"):
                add_inline(par, child, size, True, italic, color)
            elif name in ("i", "em"):
                add_inline(par, child, size, bold, True, color)
            elif name == "sup":
                run = par.add_run(clean(child.get_text()))
                set_run_font(run, size - 2, bold, italic, color)
                run.font.superscript = True
            elif name == "sub":
                run = par.add_run(clean(child.get_text()))
                set_run_font(run, size - 2, bold, italic, color)
                run.font.subscript = True
            elif name == "code":
                run = par.add_run(clean(child.get_text()))
                set_run_font(run, size - 1.6, bold, italic, color, mono=True)
            elif name == "span":
                b = "bold" in style
                c = color
                m = re.search(r"color:\s*(#[0-9A-Fa-f]{6})", style)
                if m:
                    c = RGBColor.from_string(m.group(1)[1:].upper())
                add_inline(par, child, size, bold or b, italic, c)
            else:
                add_inline(par, child, size, bold, italic, color)


def para(doc, size=BODY, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=3,
         line=1.0, keep=False, indent=None, hanging=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    pf.keep_with_next = keep
    if indent is not None:
        pf.left_indent = indent
    if hanging is not None:
        pf.first_line_indent = hanging
    return p


def set_cell_border(cell, edge="bottom", sz=4):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:color"), "000000")
    borders.append(el)


def style_table(table, n_cols):
    tbl = table._tbl
    tblPr = tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 8), ("bottom", 8), ("left", 0), ("right", 0),
                     ("insideH", 0), ("insideV", 0)):
        el = OxmlElement(f"w:{edge}")
        if sz:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(sz))
            el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)

    mar = OxmlElement("w:tblCellMar")
    for side, w in (("left", 60), ("right", 60), ("top", 30), ("bottom", 30)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(w))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    set_run_font(run, 9, color=GRAY)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


# ------------------------------------------------------------- document set-up
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin, sec.bottom_margin = Cm(1.85), Cm(1.75)
sec.left_margin = sec.right_margin = Cm(1.75)
sec.header_distance, sec.footer_distance = Cm(1.0), Cm(1.2)

def two_columns(section):
    cols = section._sectPr.xpath("./w:cols")[0]
    cols.set(qn("w:num"), "2")
    cols.set(qn("w:space"), "340")
    cols.set(qn("w:equalWidth"), "1")


def new_section(n_cols):
    """Continuous section break with n_cols columns (used for full-width tables)."""
    s = doc.add_section(WD_SECTION.CONTINUOUS)
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin, s.bottom_margin = Cm(1.85), Cm(1.75)
    s.left_margin = s.right_margin = Cm(1.75)
    cols = s._sectPr.xpath("./w:cols")[0]
    cols.set(qn("w:num"), str(n_cols))
    cols.set(qn("w:space"), "340")
    cols.set(qn("w:equalWidth"), "1")
    return s

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(BODY)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")
normal.paragraph_format.space_after = Pt(3)
normal.paragraph_format.line_spacing = 1.0

add_page_number(sec)

# -------------------------------------------------------------------- content
soup = BeautifulSoup((REPORT / "report.html").read_text(encoding="utf-8"), "html.parser")

# Word reflows differently from the browser: place Figure 6 before the full-width
# Table 4 so that the page does not end with a large empty block.
fig6 = soup.find("img", src=lambda v: v and "fig6_clusters" in v)
wide_tbl = soup.select_one("div.tabwrap.wide")
if fig6 is not None and wide_tbl is not None:
    figure = fig6.find_parent("figure")
    if figure is not None:
        figure.extract()
        wide_tbl.insert_before(figure)

# title block
tb = soup.select_one(".title-block")
if tb:
    h1 = tb.find("h1")
    p = para(doc, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, after=8, line=1.1)
    for i, chunk in enumerate(h1.get_text("\n").split("\n")):
        chunk = clean(chunk)
        if not chunk:
            continue
        if i:
            p.add_run().add_break()
        set_run_font(p.add_run(chunk), 16, bold=True)

    for sel, size in ((".authors", 11), (".affil", 9), (".corres", 8)):
        el = tb.select_one(sel)
        if el is None:
            continue
        p = para(doc, size=size, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, line=1.15)
        add_inline(p, el, size=size)
        if size == 8:
            p.paragraph_format.space_after = Pt(10)

# abstract
ab = soup.select_one(".abstract")
if ab:
    for chunk in ab.decode_contents().split("<br/>"):
        frag = BeautifulSoup(chunk, "html.parser")
        text = frag.get_text(" ", strip=True)
        if not text:
            continue
        p = para(doc, size=9.5, after=5, line=1.08)
        add_inline(p, frag, size=9.5)

# body blocks, in document order
BLOCKS = {"h2", "h3", "p", "figure", "table", "div", "ul", "ol"}
handled = set()


def walk(node):
    for child in node.children:
        if not isinstance(child, Tag) or id(child) in handled:
            continue
        cls = child.get("class", [])

        # already emitted before the walk
        if any(c in cls for c in ("title-block", "abstract")):
            continue

        if child.name == "h2":
            p = para(doc, size=10.5, align=WD_ALIGN_PARAGRAPH.LEFT, before=8, after=2, keep=True)
            set_run_font(p.add_run(clean(child.get_text())), 10.5, bold=True)

        elif child.name == "h3":
            p = para(doc, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, before=5, after=1, keep=True)
            set_run_font(p.add_run(clean(child.get_text())), 10, italic=True)

        elif child.name == "p":
            pcls = " ".join(cls)
            size = 8.3 if "refs" in str(child.parent.get("class", "")) else BODY
            if "small" in pcls:
                size = 8.6
            if "eq" in pcls:
                p = para(doc, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, before=2, after=4)
                set_run_font(p.add_run(clean(child.get_text())), 10, italic=True)
            elif "refs" in str(child.parent.get("class", "")):
                p = para(doc, size=8.3, before=0, after=3, line=1.02,
                         indent=Cm(0.42), hanging=Cm(-0.42))
                add_inline(p, child, size=8.3)
            else:
                p = para(doc, size=size, after=3)
                add_inline(p, child, size=size)

        elif child.name == "figure":
            img = child.find("img")
            cap = child.find("figcaption")
            if img is not None:
                src = Path(img["src"].replace("../", ""))
                name = src.name
                path = DOCX_FIGS.get(name, ROOT / src.as_posix())
                if Path(path).exists():
                    p = para(doc, after=2, line=1.0)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.keep_with_next = True
                    p.add_run().add_picture(str(path), width=COL_W)
            if cap is not None:
                p = para(doc, size=8.4, after=7, line=1.03)
                add_inline(p, cap, size=8.4)

        elif child.name == "div" and "tabwrap" in cls:
            cap = child.select_one(".tabcap")
            table_el = child.find("table")
            n_cols_here = 0
            if table_el is not None:
                n_cols_here = max(
                    sum(int(td.get("colspan", 1)) for td in tr.find_all(["td", "th"]))
                    for tr in table_el.find_all("tr"))
            # tables with five or more columns get the full page width
            wide = ("wide" in cls) or n_cols_here >= 5
            if wide:
                new_section(1)
            if cap is not None:
                p = para(doc, size=8.4, before=4, after=2, line=1.03, keep=True)
                add_inline(p, cap, size=8.4)
            if table_el is not None:
                build_table(table_el, total_cm=17.5 if wide else 8.45)
            if wide:
                new_section(2)

        elif child.name == "div" and "refs" in cls:
            for rp in child.find_all("p"):
                p = para(doc, size=8.3, before=0, after=3, line=1.02,
                         indent=Cm(0.42), hanging=Cm(-0.42))
                add_inline(p, rp, size=8.3)

        elif child.name in ("div", "body"):
            walk(child)


def set_table_widths(table, widths_cm):
    tbl = table._tbl
    tblPr = tbl.tblPr
    total = sum(widths_cm)
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(total / 2.54 * 1440)))

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx < len(widths_cm):
                cell.width = Cm(widths_cm[idx])


def _weights_to_widths(weights, total_cm, min_cm=1.3, max_cm=5.4):
    """Distribute the available width proportionally, clamping tiny/huge columns."""
    w = [min(max(x, 6), 30) for x in weights]
    frozen = {}
    for _ in range(30):
        free = [i for i in range(len(w)) if i not in frozen]
        avail = total_cm - sum(frozen.values())
        free_sum = sum(w[i] for i in free)
        out = dict(frozen)
        for i in free:
            out[i] = avail * w[i] / free_sum
        changed = False
        for i in free:
            if out[i] < min_cm:
                frozen[i] = min_cm
                changed = True
            elif out[i] > max_cm:
                frozen[i] = max_cm
                changed = True
        if not changed:
            return [out[i] for i in range(len(w))]
    return [total_cm / len(w)] * len(w)


def build_table(table_el, total_cm=8.45):
    rows = table_el.find_all("tr")
    n_cols = max(sum(int(td.get("colspan", 1)) for td in r.find_all(["td", "th"])) for r in rows)
    table = doc.add_table(rows=len(rows), cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    style_table(table, n_cols)

    # proportional widths so that text columns get the room they need
    max_len = [1] * n_cols
    col_of = {}
    for r, tr in enumerate(rows):
        c = 0
        for cell_el in tr.find_all(["td", "th"]):
            span = int(cell_el.get("colspan", 1))
            txt = clean(cell_el.get_text(" "))
            if span == 1:
                max_len[c] = max(max_len[c], len(txt))
            c += span
    widths = _weights_to_widths(max_len, total_cm)
    set_table_widths(table, widths)

    for r, tr in enumerate(rows):
        c = 0
        is_head = tr.find("th") is not None
        for cell_el in tr.find_all(["td", "th"]):
            span = int(cell_el.get("colspan", 1))
            cell = table.cell(r, c)
            if span > 1:
                cell = cell.merge(table.cell(r, c + span - 1))
            cell.text = ""
            text = clean(cell_el.get_text(" "))
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = (WD_ALIGN_PARAGRAPH.RIGHT if "n" in cell_el.get("class", [])
                           else WD_ALIGN_PARAGRAPH.LEFT)
            run = p.add_run(text)
            size = 7.6 if span > 1 else 8.2
            set_run_font(run, size, bold=is_head or cell_el.find("b") is not None)
            if is_head:
                set_cell_border(cell, "bottom", 4)
            tr_pr = table.rows[r]._tr.get_or_add_trPr()
            cant = OxmlElement("w:cantSplit")
            tr_pr.append(cant)
            c += span

    # keep the whole table on one page: every row but the last sticks to the next
    for row in table.rows[:-1]:
        for cell in row.cells:
            for cp in cell.paragraphs:
                cp.paragraph_format.keep_with_next = True

    # small gap after the table
    para(doc, size=4, after=6)


# body flows in a second, continuous section with two columns
body_sec = doc.add_section(WD_SECTION.CONTINUOUS)
body_sec.page_width, body_sec.page_height = Cm(21.0), Cm(29.7)
body_sec.top_margin, body_sec.bottom_margin = Cm(1.85), Cm(1.75)
body_sec.left_margin = body_sec.right_margin = Cm(1.75)
two_columns(body_sec)

walk(soup.body)

doc.save(DOCX_OUT)
print("saved", DOCX_OUT)
