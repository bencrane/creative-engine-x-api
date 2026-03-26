"""ReportLab provider wrapper.

CEX-25: Thin wrapper around ReportLab to centralise PDF generation
dependencies and provide helper utilities.
"""

from __future__ import annotations

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

__all__ = [
    "Color",
    "HexColor",
    "white",
    "TA_CENTER",
    "TA_LEFT",
    "letter",
    "ParagraphStyle",
    "getSampleStyleSheet",
    "BaseDocTemplate",
    "Frame",
    "NextPageTemplate",
    "PageBreak",
    "PageTemplate",
    "Paragraph",
    "Spacer",
    "Table",
    "TableStyle",
    "hex_to_color",
]


def hex_to_color(hex_str: str) -> Color:
    """Convert a hex colour string to a ReportLab Color."""
    return HexColor(hex_str)
