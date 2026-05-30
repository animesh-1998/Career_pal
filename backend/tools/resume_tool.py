from langchain_core.tools import tool
from llm.client import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import pdfplumber
import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import base64

llm = get_llm()

@tool
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts plain text from a base64-encoded PDF file.
    Use this first when the user uploads a resume PDF.
    Returns the extracted text content of the resume.
    """
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

@tool
def build_resume_pdf(resume_text: str) -> str:
    """
    Converts plain text resume content into a formatted PDF.
    Use this after you have modified the resume text to match the job description.
    Returns a base64-encoded PDF ready for download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
    )
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle("Name", parent=styles["Normal"], fontSize=20,
        fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4, alignment=TA_CENTER)
    contact_style = ParagraphStyle("Contact", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#555555"), spaceAfter=8, alignment=TA_CENTER)
    section_style = ParagraphStyle("Section", parent=styles["Normal"], fontSize=11,
        fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10,
        leading=14, spaceAfter=3, alignment=TA_LEFT)
    bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=10,
        leading=14, leftIndent=16, spaceAfter=2, bulletIndent=6)

    story = []
    is_first = True

    for line in resume_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        if is_first:
            story.append(Paragraph(line, name_style))
            is_first = False
            continue
        if re.search(r"[@|]|\d{3}[-.\s]\d{3}", line) and len(story) <= 2:
            story.append(Paragraph(line.replace("|", " · "), contact_style))
            continue
        if (line.isupper() and len(line) > 2) or (line.endswith(":") and len(line) < 40):
            story.append(HRFlowable(width="100%", thickness=0.5,
                color=colors.HexColor("#cccccc"), spaceAfter=4))
            story.append(Paragraph(line.rstrip(":"), section_style))
            continue
        if line.startswith(("•", "-", "*", "–")):
            story.append(Paragraph(f"• {line.lstrip('•-*– ').strip()}", bullet_style))
            continue
        story.append(Paragraph(line, body_style))

    doc.build(story)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")