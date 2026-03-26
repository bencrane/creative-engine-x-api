"""PDF renderer for lead magnets.

CEX-25: Ported from paid-engine-x app/assets/renderers/lead_magnet_pdf.py.
Renders lead magnet content as a branded multi-page PDF using ReportLab.
"""

from __future__ import annotations

import io
import logging

from src.brand.models import BrandContext
from src.generators.base import GeneratedContent
from src.providers.reportlab_provider import (
    BaseDocTemplate,
    Color,
    Frame,
    HexColor,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    ParagraphStyle,
    Spacer,
    Table,
    TableStyle,
    TA_CENTER,
    getSampleStyleSheet,
    hex_to_color,
    letter,
    white,
)
from src.renderers.base import RenderedArtifact
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_styles(primary_color: str, secondary_color: str) -> dict:
    """Build PDF paragraph styles from brand colours."""
    primary = hex_to_color(primary_color)
    secondary = hex_to_color(secondary_color)
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "PDFTitle",
            parent=base["Title"],
            fontSize=28,
            leading=34,
            textColor=white,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "PDFSubtitle",
            parent=base["Normal"],
            fontSize=14,
            leading=20,
            textColor=HexColor("#cccccc"),
            alignment=TA_CENTER,
            spaceAfter=24,
            fontName="Helvetica",
        ),
        "toc_title": ParagraphStyle(
            "TOCTitle",
            parent=base["Heading1"],
            fontSize=22,
            leading=28,
            textColor=secondary,
            spaceAfter=20,
            fontName="Helvetica-Bold",
        ),
        "toc_entry": ParagraphStyle(
            "TOCEntry",
            parent=base["Normal"],
            fontSize=12,
            leading=22,
            textColor=HexColor("#333333"),
            leftIndent=8,
            fontName="Helvetica",
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading1"],
            fontSize=20,
            leading=26,
            textColor=secondary,
            spaceBefore=16,
            spaceAfter=12,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "PDFBody",
            parent=base["Normal"],
            fontSize=11,
            leading=17,
            textColor=HexColor("#333333"),
            spaceAfter=10,
            fontName="Helvetica",
        ),
        "bullet": ParagraphStyle(
            "PDFBullet",
            parent=base["Normal"],
            fontSize=10.5,
            leading=16,
            textColor=HexColor("#444444"),
            leftIndent=20,
            bulletIndent=8,
            spaceAfter=4,
            fontName="Helvetica",
        ),
        "callout": ParagraphStyle(
            "PDFCallout",
            parent=base["Normal"],
            fontSize=10.5,
            leading=16,
            textColor=secondary,
            fontName="Helvetica-Bold",
        ),
        "footer": ParagraphStyle(
            "PDFFooter",
            parent=base["Normal"],
            fontSize=8,
            textColor=HexColor("#999999"),
            alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "_primary": primary,
        "_secondary": secondary,
    }


class _PDFDoc(BaseDocTemplate):
    def __init__(self, buf, company_name: str, primary_color: str, secondary_color: str, **kwargs):
        super().__init__(buf, **kwargs)
        self.company_name = company_name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.page_count = 0

    def afterPage(self):
        self.page_count += 1


def _cover_page(canvas, doc):
    """Draw the cover page background."""
    secondary = hex_to_color(doc.secondary_color)
    primary = hex_to_color(doc.primary_color)
    w, h = letter

    canvas.setFillColor(secondary)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    canvas.setFillColor(primary)
    canvas.rect(0, 0, w, 8, fill=1, stroke=0)

    if doc.company_name:
        canvas.setFillColor(HexColor("#888888"))
        canvas.setFont("Helvetica", 10)
        canvas.drawString(40, h - 40, doc.company_name)


def _content_page(canvas, doc):
    """Draw header/footer for content pages."""
    primary = hex_to_color(doc.primary_color)
    w, h = letter

    canvas.setStrokeColor(primary)
    canvas.setLineWidth(2)
    canvas.line(40, h - 36, w - 40, h - 36)

    if doc.company_name:
        canvas.setFillColor(HexColor("#999999"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(40, h - 30, doc.company_name)

    canvas.setFillColor(HexColor("#999999"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 28, f"Page {canvas.getPageNumber()}")

    canvas.setStrokeColor(HexColor("#e0e0e0"))
    canvas.setLineWidth(0.5)
    canvas.line(40, 44, w - 40, 44)


# ---------------------------------------------------------------------------
# PDFRenderer
# ---------------------------------------------------------------------------

class PDFRenderer:
    """Render lead magnet content as a branded PDF.

    Implements RendererProtocol. Expects content.content to have:
    - title: str
    - subtitle: str (optional)
    - sections: list of dicts with heading, body, bullets (optional), callout_box (optional)
    """

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        data = content.content
        if isinstance(data, dict):
            title = data.get("title", "Untitled")
            subtitle = data.get("subtitle")
            sections = data.get("sections", [])
        else:
            title = getattr(data, "title", "Untitled")
            subtitle = getattr(data, "subtitle", None)
            sections = getattr(data, "sections", [])

        # Extract branding
        bg = brand_context.brand_guidelines
        primary_color = bg.primary_color if bg else "#00e87b"
        secondary_color = bg.secondary_color if bg else "#09090b"
        company_name = brand_context.company_name or ""

        pdf_bytes = _render_pdf(
            title=title,
            subtitle=subtitle,
            sections=sections,
            primary_color=primary_color,
            secondary_color=secondary_color,
            company_name=company_name,
        )

        filename = f"{spec.spec_id}_{title[:30].replace(' ', '_').lower()}.pdf"

        return RenderedArtifact(
            data=pdf_bytes,
            content_type="application/pdf",
            filename=filename,
            metadata={
                "page_count": len(sections) + 2,  # cover + TOC + sections
                "renderer": "pdf",
            },
        )


def _render_pdf(
    *,
    title: str,
    subtitle: str | None,
    sections: list,
    primary_color: str,
    secondary_color: str,
    company_name: str,
) -> bytes:
    """Build the PDF document and return raw bytes."""
    buf = io.BytesIO()
    w, h = letter

    doc = _PDFDoc(
        buf,
        company_name=company_name,
        primary_color=primary_color,
        secondary_color=secondary_color,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=60,
    )

    cover_frame = Frame(40, 60, w - 80, h - 120, id="cover", showBoundary=0)
    content_frame = Frame(40, 60, w - 80, h - 110, id="content", showBoundary=0)

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=_cover_page),
        PageTemplate(id="content", frames=[content_frame], onPage=_content_page),
    ])

    styles = _build_styles(primary_color, secondary_color)
    primary = styles["_primary"]
    story = []

    # --- Cover page ---
    story.append(Spacer(1, h * 0.3))
    story.append(Paragraph(title, styles["title"]))
    if subtitle:
        story.append(Paragraph(subtitle, styles["subtitle"]))
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    # --- Table of contents ---
    story.append(Paragraph("Table of Contents", styles["toc_title"]))
    story.append(Spacer(1, 8))
    for i, section in enumerate(sections, 1):
        heading = section.get("heading", "") if isinstance(section, dict) else getattr(section, "heading", "")
        entry = f"{i}. &nbsp;&nbsp;{heading}"
        story.append(Paragraph(entry, styles["toc_entry"]))
    story.append(PageBreak())

    # --- Content sections ---
    for i, section in enumerate(sections):
        if isinstance(section, dict):
            heading = section.get("heading", "")
            body = section.get("body", "")
            bullets = section.get("bullets") or []
            callout_box = section.get("callout_box")
        else:
            heading = getattr(section, "heading", "")
            body = getattr(section, "body", "")
            bullets = getattr(section, "bullets", None) or []
            callout_box = getattr(section, "callout_box", None)

        story.append(Paragraph(heading, styles["section_heading"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(body, styles["body"]))

        if bullets:
            story.append(Spacer(1, 6))
            for bullet in bullets:
                story.append(
                    Paragraph(f"<bullet>&bull;</bullet> {bullet}", styles["bullet"])
                )
            story.append(Spacer(1, 6))

        if callout_box:
            callout_para = Paragraph(callout_box, styles["callout"])
            callout_table = Table(
                [[callout_para]],
                colWidths=[w - 100],
            )
            light_primary = Color(
                primary.red, primary.green, primary.blue, alpha=0.08
            )
            callout_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), light_primary),
                ("BOX", (0, 0), (-1, -1), 1.5, primary),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ]))
            story.append(callout_table)
            story.append(Spacer(1, 12))

        # Page break between sections (except last)
        if i < len(sections) - 1:
            story.append(PageBreak())

    doc.build(story)
    return buf.getvalue()
