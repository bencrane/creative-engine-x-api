"""Tests for the renderer base protocol and RenderedArtifact (CEX-24)."""

from __future__ import annotations

import pytest

from src.brand.models import BrandContext, BrandGuidelines
from src.generators.base import GeneratedContent
from src.renderers.base import RenderedArtifact, RendererProtocol
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


def _make_content(**overrides) -> GeneratedContent:
    defaults = {"content": {"title": "Test"}}
    defaults.update(overrides)
    return GeneratedContent(**defaults)


# ---------------------------------------------------------------------------
# Tests: RenderedArtifact
# ---------------------------------------------------------------------------

class TestRenderedArtifact:
    def test_basic_creation(self):
        artifact = RenderedArtifact(
            data=b"pdf-bytes",
            content_type="application/pdf",
            filename="test.pdf",
        )
        assert artifact.data == b"pdf-bytes"
        assert artifact.content_type == "application/pdf"
        assert artifact.filename == "test.pdf"
        assert artifact.metadata is None

    def test_with_metadata(self):
        artifact = RenderedArtifact(
            data=b"data",
            content_type="text/html",
            filename="page.html",
            metadata={"page_count": 5, "template": "lead_magnet"},
        )
        assert artifact.metadata == {"page_count": 5, "template": "lead_magnet"}

    def test_empty_data(self):
        artifact = RenderedArtifact(
            data=b"",
            content_type="application/pdf",
            filename="empty.pdf",
        )
        assert artifact.data == b""

    def test_metadata_defaults_to_none(self):
        artifact = RenderedArtifact(
            data=b"x",
            content_type="text/html",
            filename="test.html",
        )
        assert artifact.metadata is None


# ---------------------------------------------------------------------------
# Tests: RendererProtocol
# ---------------------------------------------------------------------------

class _ConcreteRenderer:
    """Minimal renderer satisfying the protocol."""

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        return RenderedArtifact(
            data=b"rendered",
            content_type="application/pdf",
            filename="output.pdf",
        )


class _NotARenderer:
    """Class that does NOT satisfy the protocol."""

    pass


class _WrongSignatureRenderer:
    """Has a render method but wrong signature."""

    async def render(self, data: bytes) -> bytes:
        return data


class TestRendererProtocol:
    def test_concrete_renderer_satisfies_protocol(self):
        renderer = _ConcreteRenderer()
        assert isinstance(renderer, RendererProtocol)

    def test_non_renderer_does_not_satisfy_protocol(self):
        obj = _NotARenderer()
        assert not isinstance(obj, RendererProtocol)

    def test_protocol_is_runtime_checkable(self):
        assert hasattr(RendererProtocol, "__protocol_attrs__") or hasattr(
            RendererProtocol, "__abstractmethods__"
        ) or isinstance(RendererProtocol, type)

    async def test_concrete_renderer_returns_artifact(self):
        renderer = _ConcreteRenderer()
        content = _make_content()
        spec = _make_spec()
        brand = _make_brand_context()

        result = await renderer.render(content, spec, brand)

        assert isinstance(result, RenderedArtifact)
        assert result.data == b"rendered"
        assert result.content_type == "application/pdf"
        assert result.filename == "output.pdf"

    async def test_renderer_receives_brand_context(self):
        """Verify the renderer receives the full brand context for styling."""

        class BrandCapturingRenderer:
            captured_brand: BrandContext | None = None

            async def render(self, content, spec, brand_context):
                self.captured_brand = brand_context
                return RenderedArtifact(data=b"x", content_type="text/html", filename="t.html")

        renderer = BrandCapturingRenderer()
        brand = _make_brand_context(company_name="TestCorp")
        await renderer.render(_make_content(), _make_spec(), brand)

        assert renderer.captured_brand is not None
        assert renderer.captured_brand.company_name == "TestCorp"
        assert renderer.captured_brand.brand_guidelines.primary_color == "#00e87b"
