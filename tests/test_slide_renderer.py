"""Tests for the slide renderer — document ads / LinkedIn carousels (CEX-26)."""

from __future__ import annotations

import re

import pytest

from src.brand.models import BrandContext, BrandGuidelines
from src.generators.base import GeneratedContent
from src.renderers.base import RenderedArtifact, RendererProtocol
from src.renderers.slide_renderer import DIMENSIONS, SCALE_BASE, SlideRenderer, _page_size
from src.specs.models import FormatSpec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_brand_context(**overrides) -> BrandContext:
    defaults = {
        "organization_id": "org-123",
        "company_name": "Acme Analytics",
        "brand_guidelines": BrandGuidelines(
            primary_color="#00e87b",
            secondary_color="#09090b",
            font_family="Inter, sans-serif",
        ),
    }
    defaults.update(overrides)
    return BrandContext(**defaults)


def _make_spec(**overrides) -> FormatSpec:
    defaults = {
        "spec_id": "document_slides__linkedin",
        "artifact_type": "document_slides",
        "surface": "linkedin",
        "version": "1.0",
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _make_content(slides=None, aspect_ratio="1:1", **overrides) -> GeneratedContent:
    if slides is None:
        slides = [
            {
                "headline": "3x Revenue Growth",
                "body": "Our platform delivers measurable results.",
                "stat_callout": "3x",
                "stat_label": "Revenue Growth",
                "is_cta_slide": False,
            },
            {
                "headline": "Cut Costs by 40%",
                "body": "Automation reduces manual effort significantly.",
                "is_cta_slide": False,
            },
            {
                "headline": "Ready to Transform?",
                "is_cta_slide": True,
                "cta_text": "Book a Demo Today",
            },
        ]
    defaults = {
        "content": {
            "slides": slides,
            "aspect_ratio": aspect_ratio,
        },
    }
    defaults.update(overrides)
    return GeneratedContent(**defaults)


def _count_pdf_pages(data: bytes) -> int:
    text = data.decode("latin-1")
    return len(re.findall(r"/Type\s*/Page\b(?!\s*s)", text))


def _get_pdf_page_dimensions(data: bytes) -> list[tuple[float, float]]:
    """Extract MediaBox dimensions from PDF."""
    text = data.decode("latin-1")
    boxes = re.findall(r"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", text)
    return [(float(b[2]), float(b[3])) for b in boxes]


# ---------------------------------------------------------------------------
# Tests: Protocol compliance
# ---------------------------------------------------------------------------

class TestSlideRendererProtocol:
    def test_satisfies_renderer_protocol(self):
        renderer = SlideRenderer()
        assert isinstance(renderer, RendererProtocol)


# ---------------------------------------------------------------------------
# Tests: Aspect ratios
# ---------------------------------------------------------------------------

class TestSlideRendererAspectRatios:
    def test_page_size_1_1(self):
        w, h = _page_size("1:1")
        assert w == 540.0
        assert h == 540.0

    def test_page_size_4_5(self):
        w, h = _page_size("4:5")
        assert w == 540.0
        assert h == 675.0

    async def test_1_1_renders_correct_dimensions(self):
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(aspect_ratio="1:1"), _make_spec(), _make_brand_context()
        )

        dims = _get_pdf_page_dimensions(result.data)
        assert len(dims) > 0
        assert dims[0] == (540.0, 540.0)

    async def test_4_5_renders_correct_dimensions(self):
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(aspect_ratio="4:5"), _make_spec(), _make_brand_context()
        )

        dims = _get_pdf_page_dimensions(result.data)
        assert len(dims) > 0
        assert dims[0] == (540.0, 675.0)


# ---------------------------------------------------------------------------
# Tests: Content slides
# ---------------------------------------------------------------------------

class TestSlideRendererContentSlides:
    async def test_renders_valid_pdf(self):
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert isinstance(result, RenderedArtifact)
        assert result.content_type == "application/pdf"
        assert result.data[:4] == b"%PDF"

    async def test_correct_page_count(self):
        """3 slides should produce 3 PDF pages."""
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        page_count = _count_pdf_pages(result.data)
        assert page_count == 3

    async def test_stat_callout_produces_content(self):
        """Slides with stat callouts should render extra content."""
        slides_with_stat = [
            {"headline": "H", "stat_callout": "99%", "stat_label": "Accuracy", "is_cta_slide": False},
        ]
        slides_without_stat = [
            {"headline": "H", "is_cta_slide": False},
        ]

        renderer = SlideRenderer()
        r_with = await renderer.render(
            _make_content(slides=slides_with_stat), _make_spec(), _make_brand_context()
        )
        r_without = await renderer.render(
            _make_content(slides=slides_without_stat), _make_spec(), _make_brand_context()
        )

        assert len(r_with.data) > len(r_without.data)


# ---------------------------------------------------------------------------
# Tests: CTA slides
# ---------------------------------------------------------------------------

class TestSlideRendererCTASlides:
    async def test_cta_slide_renders(self):
        slides = [
            {"headline": "Get Started Now", "is_cta_slide": True, "cta_text": "Learn More"},
        ]
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(slides=slides), _make_spec(), _make_brand_context()
        )

        assert result.data[:4] == b"%PDF"
        assert _count_pdf_pages(result.data) == 1

    async def test_cta_slide_without_cta_text(self):
        slides = [
            {"headline": "Contact Us", "is_cta_slide": True},
        ]
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(slides=slides), _make_spec(), _make_brand_context()
        )

        assert result.data[:4] == b"%PDF"

    async def test_mixed_content_and_cta_slides(self):
        """Mix of content and CTA slides should all render."""
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert _count_pdf_pages(result.data) == 3
        assert len(result.data) > 1000


# ---------------------------------------------------------------------------
# Tests: Branding
# ---------------------------------------------------------------------------

class TestSlideRendererBranding:
    async def test_custom_brand_colours(self):
        brand = _make_brand_context(
            brand_guidelines=BrandGuidelines(
                primary_color="#ff5500",
                secondary_color="#1a2b3c",
            )
        )
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), brand)

        assert result.data[:4] == b"%PDF"

    async def test_default_colours_when_no_guidelines(self):
        brand = _make_brand_context(brand_guidelines=None)
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), brand)

        assert result.data[:4] == b"%PDF"

    async def test_different_colours_produce_different_pdfs(self):
        brand_a = _make_brand_context(
            brand_guidelines=BrandGuidelines(primary_color="#ff0000", secondary_color="#000000")
        )
        brand_b = _make_brand_context(
            brand_guidelines=BrandGuidelines(primary_color="#0000ff", secondary_color="#333333")
        )

        renderer = SlideRenderer()
        r_a = await renderer.render(_make_content(), _make_spec(), brand_a)
        r_b = await renderer.render(_make_content(), _make_spec(), brand_b)

        assert r_a.data != r_b.data


# ---------------------------------------------------------------------------
# Tests: Slide counter
# ---------------------------------------------------------------------------

class TestSlideRendererCounter:
    async def test_slide_counter_accurate(self):
        """Metadata should report correct slide count."""
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.metadata["slide_count"] == 3

    async def test_slide_counter_with_five_slides(self):
        slides = [
            {"headline": f"Slide {i}", "is_cta_slide": False} for i in range(4)
        ] + [{"headline": "CTA", "is_cta_slide": True, "cta_text": "Go"}]

        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(slides=slides), _make_spec(), _make_brand_context()
        )

        assert result.metadata["slide_count"] == 5
        assert _count_pdf_pages(result.data) == 5


# ---------------------------------------------------------------------------
# Tests: Metadata
# ---------------------------------------------------------------------------

class TestSlideRendererMetadata:
    async def test_filename_format(self):
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.filename.endswith(".pdf")
        assert "1x1" in result.filename

    async def test_filename_4_5(self):
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(aspect_ratio="4:5"), _make_spec(), _make_brand_context()
        )

        assert "4x5" in result.filename

    async def test_metadata_aspect_ratio(self):
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.metadata["aspect_ratio"] == "1:1"

    async def test_metadata_renderer_tag(self):
        renderer = SlideRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.metadata["renderer"] == "slide"


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestSlideRendererEdgeCases:
    async def test_single_slide(self):
        slides = [{"headline": "Solo Slide", "body": "Single content.", "is_cta_slide": False}]
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(slides=slides), _make_spec(), _make_brand_context()
        )

        assert result.data[:4] == b"%PDF"
        assert _count_pdf_pages(result.data) == 1

    async def test_many_slides(self):
        slides = [{"headline": f"S{i}", "is_cta_slide": False} for i in range(8)]
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(slides=slides), _make_spec(), _make_brand_context()
        )

        assert _count_pdf_pages(result.data) == 8
        assert result.metadata["slide_count"] == 8

    async def test_slide_with_all_fields(self):
        slides = [
            {
                "headline": "Full Slide",
                "body": "Complete body text.",
                "stat_callout": "100%",
                "stat_label": "Satisfaction",
                "is_cta_slide": False,
            }
        ]
        renderer = SlideRenderer()
        result = await renderer.render(
            _make_content(slides=slides), _make_spec(), _make_brand_context()
        )

        assert result.data[:4] == b"%PDF"
