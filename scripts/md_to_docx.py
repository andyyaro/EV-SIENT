"""Markdown → styled DOCX converter for the final reports (headings, tables,
blockquotes, lists, bold/italic inline)."""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

GREEN = RGBColor(0x1B, 0x43, 0x32)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GOLD = RGBColor(0x7A, 0x5B, 0x00)


def add_inline(par, text, size=10.5, color=BLACK, italic=False):
    for part in re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); r.font.name = "Courier New"
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            r = par.add_run(part)
        r.font.size = Pt(size)
        r.font.color.rgb = color
        if italic:
            r.italic = True


def convert(md_path: Path, docx_path: Path):
    # `landscape_tables=False` removed: the body never read it and no caller passed it.
    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Inches(0.7)

    lines = md_path.read_text().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip("|").split("|")]
                rows.append(cells)
                i += 1
            rows.pop(1)  # separator
            ncols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=ncols)
            table.style = "Light Grid Accent 3"
            for ri, row in enumerate(rows):
                for ci in range(ncols):
                    cell = table.cell(ri, ci)
                    cell.paragraphs[0].text = ""
                    txt = row[ci] if ci < len(row) else ""
                    add_inline(cell.paragraphs[0], txt, size=8 if ncols > 5 else 9.5,
                               color=GREEN if ri == 0 else BLACK)
                    if ri == 0:
                        for r in cell.paragraphs[0].runs:
                            r.bold = True
            doc.add_paragraph()
            continue

        if line.startswith("# "):
            p = doc.add_heading(level=0); p.text = ""
            add_inline(p, line[2:], size=20, color=GREEN)
        elif line.startswith("## "):
            p = doc.add_heading(level=1); p.text = ""
            add_inline(p, line[3:], size=15, color=GREEN)
        elif line.startswith("### "):
            p = doc.add_heading(level=2); p.text = ""
            add_inline(p, line[4:], size=12.5, color=GREEN)
        elif line.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            add_inline(p, line[2:], size=10, color=GOLD, italic=True)
        elif line.startswith("- ") or line.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, line[2:])
        elif re.match(r"^\d+\. ", line):
            p = doc.add_paragraph(style="List Number")
            add_inline(p, re.sub(r"^\d+\. ", "", line))
        elif line.strip() in ("---", "***"):
            doc.add_paragraph("_" * 60)
        elif line.strip():
            p = doc.add_paragraph()
            add_inline(p, line)
        i += 1

    doc.save(docx_path)
    print("wrote", docx_path)


if __name__ == "__main__":
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
