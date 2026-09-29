"""Generate public/files/cv.pdf from the same YAML used by the CV page.

Requires Node.js (for the site's yaml dependency) and Python's reportlab package.
Run from the repository root: python scripts/generate_cv_pdf.py
"""

import json
import subprocess
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "files" / "cv.pdf"
RED = colors.HexColor("#9e2430")
INK = colors.HexColor("#20232a")
MUTED = colors.HexColor("#59616d")


def read_site_data():
    js = """
      import fs from 'node:fs';
      import yaml from 'yaml';
      const read = file => yaml.parse(fs.readFileSync(file, 'utf8'));
      console.log(JSON.stringify({config: read('site.config.yml'), cv: read('src/content/cv/cv.yml')}));
    """
    result = subprocess.run(
        ["node", "--input-type=module", "-e", js],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def register_fonts():
    candidates = [
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("CVSans", str(regular)))
            pdfmetrics.registerFont(TTFont("CVSans-Bold", str(bold)))
            pdfmetrics.registerFontFamily("CVSans", normal="CVSans", bold="CVSans-Bold")
            return "CVSans", "CVSans-Bold"
    raise RuntimeError("No Unicode font found. Install Arial or DejaVu Sans.")


def clean(value):
    return escape(str(value or "")).replace("–", "-").replace("—", "-")


def main():
    data = read_site_data()
    config, cv = data["config"], data["cv"]
    regular, bold = register_fonts()
    name = config["profile"]["name"]
    site_url = config["site"]["url"]
    email = config["profile"]["email"]

    title = ParagraphStyle("title", fontName=bold, fontSize=21, leading=25, textColor=INK, spaceAfter=5)
    contact = ParagraphStyle("contact", fontName=regular, fontSize=9, leading=14, textColor=MUTED)
    section = ParagraphStyle("section", fontName=bold, fontSize=11, leading=15, textColor=RED, spaceBefore=16, spaceAfter=6)
    item_title = ParagraphStyle("item_title", fontName=bold, fontSize=9.5, leading=13, textColor=INK, spaceAfter=1)
    item_meta = ParagraphStyle("item_meta", fontName=regular, fontSize=9, leading=12.5, textColor=MUTED, spaceAfter=2)
    body = ParagraphStyle("body", fontName=regular, fontSize=9, leading=13, textColor=INK)

    story = [
        Paragraph(clean(name), title),
        Paragraph(f"{clean(config['profile']['position'])}  |  {clean(config['profile']['university'])}", contact),
        Paragraph(f"{clean(email)}  |  {clean(site_url)}", contact),
        Spacer(1, 13),
        HRFlowable(width="100%", thickness=1.2, color=RED),
    ]

    def heading(text):
        story.append(Paragraph(text, section))

    def entry(primary, secondary, description=None):
        parts = [Paragraph(clean(primary), item_title), Paragraph(clean(secondary), item_meta)]
        if description:
            parts.append(Paragraph(clean(description), body))
        parts.append(Spacer(1, 8))
        story.append(KeepTogether(parts))

    if cv.get("education"):
        heading("EDUCATION")
        for row in cv["education"]:
            entry(row["degree"], f"{row['institution']}  |  {row['year']}", row.get("description"))

    if cv.get("experience"):
        heading("EXPERIENCE")
        for row in cv["experience"]:
            entry(row["title"], f"{row['organization']}  |  {row['start_date']} - {row['end_date']}", row.get("description"))

    if cv.get("awards"):
        story.append(PageBreak())
        heading("AWARDS & HONORS")
        for row in cv["awards"]:
            entry(row["title"], f"{row['organization']}  |  {row['year']}")

    if cv.get("service"):
        heading("PROFESSIONAL SERVICE")
        for row in cv["service"]:
            entry(row["role"], f"{row['organization']}  |  {row['years']}")

    if cv.get("skills"):
        heading("SKILLS")
        for row in cv["skills"]:
            entry(row["category"], ", ".join(row["items"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=44,
        bottomMargin=48,
        title=f"Curriculum Vitae - {name}",
        author=name,
    )

    def page_footer(canvas, document):
        canvas.saveState()
        canvas.setFont(regular, 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(A4[0] - 48, 26, f"{name}  |  {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
