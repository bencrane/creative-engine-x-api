"""Slide renderer for document ads / LinkedIn carousels.

CEX-26: Ported from paid-engine-x app/assets/renderers/document_ad_pdf.py.
Each slide is one PDF page. Supports 1:1 (540x540pt) and 4:5 (540x675pt) ratios.
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
    TA_CENTER,
    TA_LEFT,
    hex_to_color,
    white,
)
from src.renderers.base import RenderedArtifact
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)

# Pixel dimensions for each aspect ratio
DIMENSIONS = {
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

# Scale 1080px to 7.5 inches (540 points) for readability
SCALE_BASE = 7.5 * 72  # 540 points


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _page_size(aspect_ratio: str) -> tuple[float, float]:
    px_w, px_h = DIMENSIONS.get(aspect_ratio, DIMENSIONS["1:1"])
    w = SCALE_BASE
    h = w * (px_h / px_w)
    return (w, h)


def _build_slide_styles(primary_color: str, secondary_color: str) -> dict:
    secondary = hex_to_color(secondary_color)
    return {
        "headline": ParagraphStyle(
            "SlideHeadline",
            fontSize=32,
            leading=40,
            textColor=white,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT,
            spaceAfter=16,
        ),
        "body": ParagraphStyle(
            "SlideBody",
            fontSize=16,
            leading=24,
            textColor=HexColor("#dddddd"),
            fontName="Helvetica",
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "stat": ParagraphStyle(
            "SlideStat",
            fontSize=72,
            leading=80,
            textColor=hex_to_color(primary_color),
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "stat_label": ParagraphStyle(
            "SlideStatLabel",
            fontSize=18,
            leading=24,
            textColor=HexColor("#cccccc"),
            fontName="Helvetica",
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "cta_headline": ParagraphStyle(
            "CTAHeadline",
            fontSize=36,
            leading=44,
            textColor=white,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            spaceAfter=24,
        ),
        "cta_text": ParagraphStyle(
            "CTAText",
            fontSize=20,
            leading=28,
            textColor=secondary,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
    }


class _SlideDoc(BaseDocTemplate):
    def __init__(self, buf, slides, company_name, primary_color, secondary_color, **kwargs):
        super().__init__(buf, **kwargs)
        self.slide_list = slides
        self.company_name = company_name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self._slide_idx = 0

    def afterPage(self):
        self._slide_idx += 1


def _draw_slide_bg(canvas, doc):
    """Dark background with branding accent."""
    secondary = hex_to_color(doc.secondary_color)
    primary = hex_to_color(doc.primary_color)
    w, h = doc.pagesize

    canvas.setFillColor(secondary)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Accent bar at top
    canvas.setFillColor(primary)
    canvas.rect(0, h - 6, w, 6, fill=1, stroke=0)

    # Company name bottom-right
    if doc.company_name:
        canvas.setFillColor(HexColor("#666666"))
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - 28, 20, doc.company_name)

    # Slide number bottom-left
    canvas.setFillColor(HexColor("#555555"))
    canvas.setFont("Helvetica", 9)
    page_num = canvas.getPageNumber()
    total = len(doc.slide_list)
    canvas.drawString(28, 20, f"{page_num}/{total}")


def _draw_cta_bg(canvas, doc):
    """CTA slide with translucent accent circle."""
    primary = hex_to_color(doc.primary_color)
    secondary = hex_to_color(doc.secondary_color)
    w, h = doc.pagesize

    canvas.setFillColor(secondary)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Large accent circle in center
    canvas.setFillColor(Color(primary.red, primary.green, primary.blue, alpha=0.12))
    canvas.circle(w / 2, h / 2, w * 0.35, fill=1, stroke=0)

    # Company name
    if doc.company_name:
        canvas.setFillColor(HexColor("#666666"))
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - 28, 20, doc.company_name)


# ---------------------------------------------------------------------------
# SlideRenderer
# ---------------------------------------------------------------------------

class SlideRenderer:
    """Render document ad slides as a branded PDF.

    Implements RendererProtocol. Expects content.content to have:
    - slides: list of dicts with headline, body, stat_callout, stat_label,
              is_cta_slide, cta_text
    - aspect_ratio: "1:1" or "4:5" (optional, defaults to "1:1")
    """

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        data = content.content
        if isinstance(data, dict):
            slides = data.get("slides", [])
            aspect_ratio = data.get("aspect_ratio", "1:1")
        else:
            slides = getattr(data, "slides", [])
            aspect_ratio = getattr(data, "aspect_ratio", "1:1")

        # Extract branding
        bg = brand_context.brand_guidelines
        primary_color = bg.primary_color if bg else "#00e87b"
        secondary_color = bg.secondary_color if bg else "#09090b"
        company_name = brand_context.company_name or ""

        pdf_bytes = _render_slides(
            slides=slides,
            aspect_ratio=aspect_ratio,
            primary_color=primary_color,
            secondary_color=secondary_color,
            company_name=company_name,
        )

        return RenderedArtifact(
            data=pdf_bytes,
            content_type="application/pdf",
            filename=f"{spec.spec_id}_slides_{aspect_ratio.replace(':', 'x')}.pdf",
            metadata={
                "slide_count": len(slides),
                "aspect_ratio": aspect_ratio,
                "renderer": "slide",
            },
        )


def _render_slides(
    *,
    slides: list,
    aspect_ratio: str,
    primary_color: str,
    secondary_color: str,
    company_name: str,
) -> bytes:
    """Build the slide PDF and return raw bytes."""
    buf = io.BytesIO()
    page_w, page_h = _page_size(aspect_ratio)

    doc = _SlideDoc(
        buf,
        slides=slides,
        company_name=company_name,
        primary_color=primary_color,
        secondary_color=secondary_color,
        pagesize=(page_w, page_h),
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=48,
    )

    margin = 40
    frame_w = page_w - 2 * margin
    frame_h = page_h - 88  # top + bottom margins

    templates = []
    for i, slide in enumerate(slides):
        is_cta = slide.get("is_cta_slide", False) if isinstance(slide, dict) else getattr(slide, "is_cta_slide", False)
        bg_fn = _draw_cta_bg if is_cta else _draw_slide_bg
        templates.append(
            PageTemplate(
                id=f"slide_{i}",
                frames=[Frame(margin, 48, frame_w, frame_h, showBoundary=0)],
                onPage=bg_fn,
            )
        )
    doc.addPageTemplates(templates)

    styles = _build_slide_styles(primary_color, secondary_color)
    story = []

    for i, slide in enumerate(slides):
        if isinstance(slide, dict):
            headline = slide.get("headline", "")
            body = slide.get("body")
            stat_callout = slide.get("stat_callout")
            stat_label = slide.get("stat_label")
            is_cta = slide.get("is_cta_slide", False)
            cta_text = slide.get("cta_text")
        else:
            headline = getattr(slide, "headline", "")
            body = getattr(slide, "body", None)
            stat_callout = getattr(slide, "stat_callout", None)
            stat_label = getattr(slide, "stat_label", None)
            is_cta = getattr(slide, "is_cta_slide", False)
            cta_text = getattr(slide, "cta_text", None)

        if i > 0:
            story.append(NextPageTemplate(f"slide_{i}"))
            story.append(PageBreak())

        if is_cta:
            story.append(Spacer(1, frame_h * 0.25))
            story.append(Paragraph(headline, styles["cta_headline"]))
            if cta_text:
                story.append(Spacer(1, 16))
                story.append(Paragraph(cta_text, styles["cta_text"]))
        else:
            story.append(Spacer(1, frame_h * 0.08))

            if stat_callout:
                story.append(Paragraph(stat_callout, styles["stat"]))
                if stat_label:
                    story.append(Paragraph(stat_label, styles["stat_label"]))
                story.append(Spacer(1, 16))

            story.append(Paragraph(headline, styles["headline"]))

            if body:
                story.append(Paragraph(body, styles["body"]))

    doc.build(story)
    return buf.getvalue()
