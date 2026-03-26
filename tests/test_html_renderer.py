"""Tests for the HTML renderer — landing pages + Jinja2 templates (CEX-27)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.brand.models import BrandContext, BrandGuidelines
from src.generators.base import GeneratedContent
from src.renderers.base import RenderedArtifact, RendererProtocol
from src.renderers.html_renderer import HTMLRenderer, VALID_TEMPLATES
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
            logo_url="https://example.com/logo.png",
        ),
    }
    defaults.update(overrides)
    return BrandContext(**defaults)


def _make_spec(**overrides) -> FormatSpec:
    defaults = {
        "spec_id": "html_page__landing",
        "artifact_type": "html_page",
        "surface": "landing",
        "version": "1.0",
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _make_lead_magnet_content(**overrides) -> GeneratedContent:
    defaults = {
        "content": {
            "template": "lead_magnet_download",
            "slug": "analytics-guide",
            "headline": "The Ultimate Analytics Guide",
            "subhead": "Everything you need to know about modern analytics",
            "value_props": ["Save 40 hours/month", "Real-time dashboards", "No coding required"],
            "form_fields": [
                {"name": "email", "label": "Work Email", "type": "email", "required": True},
                {"name": "name", "label": "Full Name", "type": "text", "required": True},
            ],
            "cta_text": "Download Now",
        },
    }
    defaults.update(overrides)
    return GeneratedContent(**defaults)


def _make_case_study_content(**overrides) -> GeneratedContent:
    defaults = {
        "content": {
            "template": "case_study",
            "slug": "bigco-success",
            "headline": "How BigCo Achieved 3x ROI",
            "customer_name": "BigCo Industries",
            "customer_logo_url": "https://example.com/bigco.png",
            "sections": [
                {"heading": "The Challenge", "body": "Manual reporting wasted 40 hours/month."},
                {"heading": "The Solution", "body": "Acme Analytics automated everything."},
            ],
            "metrics": [
                {"value": "3x", "label": "ROI"},
                {"value": "40hrs", "label": "Saved/Month"},
            ],
            "quote_text": "This transformed our business.",
            "quote_author": "Jane Doe",
            "quote_title": "VP of Sales",
            "cta_text": "Get Similar Results",
            "form_fields": [
                {"name": "email", "label": "Work Email", "type": "email", "required": True},
            ],
        },
    }
    defaults.update(overrides)
    return GeneratedContent(**defaults)


def _make_webinar_content(**overrides) -> GeneratedContent:
    defaults = {
        "content": {
            "template": "webinar",
            "slug": "ai-analytics-webinar",
            "event_name": "AI-Powered Analytics Summit",
            "event_date": "March 30, 2026",
            "headline": "Master AI-Powered Analytics",
            "speakers": [
                {"name": "Dr. Smith", "title": "Chief Data Scientist", "company": "Acme"},
            ],
            "agenda": ["Opening keynote", "Live demo", "Q&A session"],
            "form_fields": [
                {"name": "email", "label": "Work Email", "type": "email", "required": True},
                {"name": "name", "label": "Full Name", "type": "text", "required": True},
            ],
            "cta_text": "Register Now",
        },
    }
    defaults.update(overrides)
    return GeneratedContent(**defaults)


def _make_demo_request_content(**overrides) -> GeneratedContent:
    defaults = {
        "content": {
            "template": "demo_request",
            "slug": "demo",
            "headline": "See Acme Analytics in Action",
            "subhead": "Get a personalized demo from our team",
            "benefits": [
                {"heading": "Real-time", "body": "Live dashboards updated instantly."},
                {"heading": "Automated", "body": "No manual reporting needed."},
                {"heading": "Scalable", "body": "Grows with your business."},
            ],
            "form_fields": [
                {"name": "email", "label": "Work Email", "type": "email", "required": True},
                {"name": "name", "label": "Full Name", "type": "text", "required": True},
                {"name": "company", "label": "Company", "type": "text", "required": True},
            ],
            "cta_text": "Request Demo",
        },
    }
    defaults.update(overrides)
    return GeneratedContent(**defaults)


# ---------------------------------------------------------------------------
# Tests: Protocol compliance
# ---------------------------------------------------------------------------

class TestHTMLRendererProtocol:
    def test_satisfies_renderer_protocol(self):
        renderer = HTMLRenderer()
        assert isinstance(renderer, RendererProtocol)


# ---------------------------------------------------------------------------
# Tests: All 4 templates render correctly
# ---------------------------------------------------------------------------

class TestHTMLRendererTemplates:
    async def test_lead_magnet_download_renders(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        assert isinstance(result, RenderedArtifact)
        assert result.content_type == "text/html"
        html = result.data.decode("utf-8")
        assert "<!DOCTYPE html>" in html
        assert "The Ultimate Analytics Guide" in html

    async def test_case_study_renders(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_case_study_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "<!DOCTYPE html>" in html
        assert "How BigCo Achieved 3x ROI" in html
        assert "BigCo Industries" in html

    async def test_webinar_renders(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_webinar_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "<!DOCTYPE html>" in html
        assert "Master AI-Powered Analytics" in html
        assert "March 30, 2026" in html

    async def test_demo_request_renders(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_demo_request_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "<!DOCTYPE html>" in html
        assert "See Acme Analytics in Action" in html


# ---------------------------------------------------------------------------
# Tests: Branding colours and fonts
# ---------------------------------------------------------------------------

class TestHTMLRendererBranding:
    async def test_primary_colour_applied(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "#00e87b" in html

    async def test_secondary_colour_applied(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "#09090b" in html

    async def test_font_family_applied(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "Inter, sans-serif" in html

    async def test_company_name_in_title(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "Acme Analytics" in html

    async def test_logo_url_rendered(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "https://example.com/logo.png" in html

    async def test_custom_brand_colours(self):
        brand = _make_brand_context(
            brand_guidelines=BrandGuidelines(
                primary_color="#ff5500",
                secondary_color="#1a2b3c",
                font_family="Roboto, sans-serif",
            )
        )
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), brand
        )

        html = result.data.decode("utf-8")
        assert "#ff5500" in html
        assert "#1a2b3c" in html
        assert "Roboto, sans-serif" in html


# ---------------------------------------------------------------------------
# Tests: Form fields per template
# ---------------------------------------------------------------------------

class TestHTMLRendererForms:
    async def test_lead_magnet_form_fields(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert 'name="email"' in html
        assert 'name="name"' in html
        assert 'type="email"' in html

    async def test_case_study_form_fields(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_case_study_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert 'name="email"' in html

    async def test_webinar_form_fields(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_webinar_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert 'name="email"' in html
        assert 'name="name"' in html

    async def test_demo_request_form_fields(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_demo_request_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert 'name="email"' in html
        assert 'name="company"' in html


# ---------------------------------------------------------------------------
# Tests: Mobile responsive layout
# ---------------------------------------------------------------------------

class TestHTMLRendererResponsive:
    async def test_has_viewport_meta(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "viewport" in html
        assert "width=device-width" in html

    async def test_has_media_queries(self):
        renderer = HTMLRenderer()
        for content_fn in [_make_lead_magnet_content, _make_case_study_content,
                          _make_webinar_content, _make_demo_request_content]:
            result = await renderer.render(content_fn(), _make_spec(), _make_brand_context())
            html = result.data.decode("utf-8")
            assert "@media" in html
            assert "768px" in html


# ---------------------------------------------------------------------------
# Tests: RudderStack SDK injection
# ---------------------------------------------------------------------------

class TestHTMLRendererRudderStack:
    async def test_rudderstack_injected_when_configured(self):
        with patch("src.renderers.html_renderer.settings") as mock_settings:
            mock_settings.rudderstack_write_key = "test-write-key"
            mock_settings.rudderstack_data_plane_url = "https://rs.example.com"

            renderer = HTMLRenderer()
            result = await renderer.render(
                _make_lead_magnet_content(), _make_spec(), _make_brand_context()
            )

        html = result.data.decode("utf-8")
        assert "rudderanalytics" in html
        assert "test-write-key" in html

    async def test_rudderstack_not_injected_when_empty(self):
        with patch("src.renderers.html_renderer.settings") as mock_settings:
            mock_settings.rudderstack_write_key = ""
            mock_settings.rudderstack_data_plane_url = ""

            renderer = HTMLRenderer()
            result = await renderer.render(
                _make_lead_magnet_content(), _make_spec(), _make_brand_context()
            )

        html = result.data.decode("utf-8")
        # The SDK snippet should NOT be rendered (conditional block skipped)
        assert "rudderanalytics.load" not in html


# ---------------------------------------------------------------------------
# Tests: UTM capture
# ---------------------------------------------------------------------------

class TestHTMLRendererUTM:
    async def test_utm_hidden_fields_present(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert 'name="utm_source"' in html
        assert 'name="utm_medium"' in html
        assert 'name="utm_campaign"' in html

    async def test_utm_javascript_capture(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "URLSearchParams" in html
        assert "utm_source" in html


# ---------------------------------------------------------------------------
# Tests: HTML validity
# ---------------------------------------------------------------------------

class TestHTMLRendererValidity:
    async def test_has_doctype(self):
        renderer = HTMLRenderer()
        for content_fn in [_make_lead_magnet_content, _make_case_study_content,
                          _make_webinar_content, _make_demo_request_content]:
            result = await renderer.render(content_fn(), _make_spec(), _make_brand_context())
            html = result.data.decode("utf-8")
            assert html.strip().startswith("<!DOCTYPE html>")

    async def test_has_closing_html_tag(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert "</html>" in html

    async def test_has_form_action(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        html = result.data.decode("utf-8")
        assert '/lp/analytics-guide/submit' in html


# ---------------------------------------------------------------------------
# Tests: Metadata
# ---------------------------------------------------------------------------

class TestHTMLRendererMetadata:
    async def test_filename_uses_slug(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        assert result.filename == "analytics-guide.html"

    async def test_filename_fallback_to_template(self):
        content = GeneratedContent(
            content={"template": "demo_request", "headline": "H", "subhead": "S",
                     "benefits": [], "form_fields": [], "cta_text": "Go"}
        )
        renderer = HTMLRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.filename == "demo_request.html"

    async def test_metadata_template_name(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        assert result.metadata["template"] == "lead_magnet_download"

    async def test_metadata_renderer_tag(self):
        renderer = HTMLRenderer()
        result = await renderer.render(
            _make_lead_magnet_content(), _make_spec(), _make_brand_context()
        )

        assert result.metadata["renderer"] == "html"


# ---------------------------------------------------------------------------
# Tests: Valid template names
# ---------------------------------------------------------------------------

class TestHTMLRendererTemplateNames:
    def test_valid_templates_set(self):
        assert "lead_magnet_download" in VALID_TEMPLATES
        assert "case_study" in VALID_TEMPLATES
        assert "webinar" in VALID_TEMPLATES
        assert "demo_request" in VALID_TEMPLATES
        assert len(VALID_TEMPLATES) == 4

    async def test_invalid_template_falls_back(self):
        content = GeneratedContent(
            content={"template": "nonexistent", "slug": "test", "headline": "H",
                     "subhead": "S", "value_props": [], "form_fields": [], "cta_text": "Go"}
        )
        renderer = HTMLRenderer()
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.metadata["template"] == "lead_magnet_download"
