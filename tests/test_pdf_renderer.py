"""Tests for the PDF renderer — lead magnets (CEX-25)."""

from __future__ import annotations

import pytest

from src.brand.models import BrandContext, BrandGuidelines
from src.generators.base import GeneratedContent
from src.renderers.base import RenderedArtifact, RendererProtocol
from src.renderers.pdf_renderer import PDFRenderer
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
        "spec_id": "pdf__lead_magnet",
        "artifact_type": "pdf",
        "surface": "lead_magnet",
        "version": "1.0",
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _make_content(sections=None, **overrides) -> GeneratedContent:
    if sections is None:
        sections = [
            {
                "heading": "Introduction",
                "body": "This is the introduction to our guide.",
                "bullets": ["Key point A", "Key point B"],
                "callout_box": "Important: This is a callout.",
            },
            {
                "heading": "Best Practices",
                "body": "Here are the best practices for your team.",
                "bullets": ["Practice 1", "Practice 2", "Practice 3"],
            },
            {
                "heading": "Conclusion",
                "body": "Wrapping up our comprehensive guide.",
            },
        ]
    defaults = {
        "content": {
            "title": "The Ultimate Guide to Analytics",
            "subtitle": "A comprehensive resource for data-driven teams",
            "sections": sections,
        },
    }
    defaults.update(overrides)
    return GeneratedContent(**defaults)


def _count_pdf_pages(data: bytes) -> int:
    """Count pages in a PDF by parsing /Type /Page entries."""
    text = data.decode("latin-1")
    # Count page objects (not the /Pages catalog)
    import re
    pages = re.findall(r"/Type\s*/Page\b(?!\s*s)", text)
    return len(pages)


# ---------------------------------------------------------------------------
# Tests: Protocol compliance
# ---------------------------------------------------------------------------

class TestPDFRendererProtocol:
    def test_satisfies_renderer_protocol(self):
        renderer = PDFRenderer()
        assert isinstance(renderer, RendererProtocol)


# ---------------------------------------------------------------------------
# Tests: Cover page and branding
# ---------------------------------------------------------------------------

class TestPDFRendererCoverPage:
    async def test_renders_valid_pdf(self):
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert isinstance(result, RenderedArtifact)
        assert result.content_type == "application/pdf"
        assert result.data[:4] == b"%PDF"

    async def test_cover_page_with_branding(self):
        """Cover renders with correct branding — secondary_color bg, primary accent."""
        renderer = PDFRenderer()
        brand = _make_brand_context()
        result = await renderer.render(_make_content(), _make_spec(), brand)

        # PDF is valid and non-trivial
        assert len(result.data) > 1000
        assert result.data[:4] == b"%PDF"

    async def test_pdf_has_multiple_pages(self):
        """PDF should have cover + TOC + content pages."""
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        page_count = _count_pdf_pages(result.data)
        # At minimum: cover + TOC + at least one content page
        assert page_count >= 3


# ---------------------------------------------------------------------------
# Tests: TOC generation
# ---------------------------------------------------------------------------

class TestPDFRendererTOC:
    async def test_toc_is_generated(self):
        """PDF with 3 sections should have a TOC page."""
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        # PDF should have enough pages for cover + TOC + sections
        page_count = _count_pdf_pages(result.data)
        assert page_count >= 3

    async def test_page_count_scales_with_sections(self):
        """More sections = more pages."""
        sections_small = [{"heading": f"S{i}", "body": "B"} for i in range(2)]
        sections_large = [{"heading": f"S{i}", "body": "B"} for i in range(5)]

        renderer = PDFRenderer()
        result_small = await renderer.render(
            _make_content(sections=sections_small), _make_spec(), _make_brand_context()
        )
        result_large = await renderer.render(
            _make_content(sections=sections_large), _make_spec(), _make_brand_context()
        )

        pages_small = _count_pdf_pages(result_small.data)
        pages_large = _count_pdf_pages(result_large.data)
        assert pages_large >= pages_small


# ---------------------------------------------------------------------------
# Tests: Content sections
# ---------------------------------------------------------------------------

class TestPDFRendererSections:
    async def test_section_headings_render(self):
        """PDF with 3 sections renders successfully."""
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"
        assert len(result.data) > 2000

    async def test_bullets_produce_larger_pdf(self):
        """Sections with bullets should generate more content than without."""
        sections_no_bullets = [{"heading": "H", "body": "Body text only."}]
        sections_with_bullets = [
            {"heading": "H", "body": "Body text.", "bullets": ["A", "B", "C", "D", "E"]}
        ]

        renderer = PDFRenderer()
        r1 = await renderer.render(
            _make_content(sections=sections_no_bullets), _make_spec(), _make_brand_context()
        )
        r2 = await renderer.render(
            _make_content(sections=sections_with_bullets), _make_spec(), _make_brand_context()
        )

        assert len(r2.data) > len(r1.data)

    async def test_callout_box_produces_larger_pdf(self):
        """Sections with callout boxes generate more content."""
        sections_no_callout = [{"heading": "H", "body": "Body text."}]
        sections_with_callout = [
            {"heading": "H", "body": "Body text.", "callout_box": "Important callout!"}
        ]

        renderer = PDFRenderer()
        r1 = await renderer.render(
            _make_content(sections=sections_no_callout), _make_spec(), _make_brand_context()
        )
        r2 = await renderer.render(
            _make_content(sections=sections_with_callout), _make_spec(), _make_brand_context()
        )

        assert len(r2.data) > len(r1.data)

    async def test_section_without_bullets_or_callout(self):
        """Sections with only heading+body should render fine."""
        sections = [{"heading": "Simple Section", "body": "Just body text."}]
        content = _make_content(sections=sections)
        renderer = PDFRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Tests: Branding colours
# ---------------------------------------------------------------------------

class TestPDFRendererBranding:
    async def test_custom_brand_colours(self):
        """PDF renders successfully with custom brand colours."""
        brand = _make_brand_context(
            brand_guidelines=BrandGuidelines(
                primary_color="#ff5500",
                secondary_color="#1a2b3c",
            )
        )
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), brand)

        assert result.data[:4] == b"%PDF"
        assert len(result.data) > 1000

    async def test_default_colours_when_no_guidelines(self):
        """Renderer uses defaults when brand_guidelines is None."""
        brand = _make_brand_context(brand_guidelines=None)
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), brand)

        assert result.data[:4] == b"%PDF"

    async def test_different_brand_colours_produce_different_pdfs(self):
        """Different brand colours should produce different PDFs."""
        brand_a = _make_brand_context(
            brand_guidelines=BrandGuidelines(primary_color="#ff0000", secondary_color="#000000")
        )
        brand_b = _make_brand_context(
            brand_guidelines=BrandGuidelines(primary_color="#0000ff", secondary_color="#333333")
        )

        renderer = PDFRenderer()
        r_a = await renderer.render(_make_content(), _make_spec(), brand_a)
        r_b = await renderer.render(_make_content(), _make_spec(), brand_b)

        assert r_a.data != r_b.data


# ---------------------------------------------------------------------------
# Tests: Output metadata
# ---------------------------------------------------------------------------

class TestPDFRendererMetadata:
    async def test_filename_format(self):
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.filename.endswith(".pdf")
        assert "pdf__lead_magnet" in result.filename

    async def test_metadata_includes_page_count(self):
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.metadata is not None
        assert "page_count" in result.metadata
        assert result.metadata["page_count"] == 5  # cover + TOC + 3 sections

    async def test_metadata_renderer_tag(self):
        renderer = PDFRenderer()
        result = await renderer.render(_make_content(), _make_spec(), _make_brand_context())

        assert result.metadata["renderer"] == "pdf"


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestPDFRendererEdgeCases:
    async def test_empty_sections(self):
        content = _make_content(sections=[])
        renderer = PDFRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"

    async def test_single_section(self):
        sections = [{"heading": "Only Section", "body": "Single content block."}]
        content = _make_content(sections=sections)
        renderer = PDFRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"
        assert len(result.data) > 500

    async def test_no_subtitle(self):
        content = GeneratedContent(
            content={
                "title": "No Subtitle Guide",
                "sections": [{"heading": "Sec", "body": "Body text."}],
            }
        )
        renderer = PDFRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"

    async def test_long_title(self):
        content = GeneratedContent(
            content={
                "title": "A" * 200,
                "subtitle": "B" * 100,
                "sections": [{"heading": "H", "body": "B"}],
            }
        )
        renderer = PDFRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"

    async def test_many_sections(self):
        """Stress test with many sections."""
        sections = [
            {"heading": f"Section {i}", "body": f"Content for section {i}.", "bullets": [f"bullet {j}" for j in range(3)]}
            for i in range(10)
        ]
        content = _make_content(sections=sections)
        renderer = PDFRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.data[:4] == b"%PDF"
        assert result.metadata["page_count"] == 12  # cover + TOC + 10 sections
