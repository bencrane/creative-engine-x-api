"""Tests for landing page hosting — /lp/{slug} serving and form submission (CEX-28)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.landing_pages.router import router, _get_artifact_by_slug


# ---------------------------------------------------------------------------
# Fixtures: mock DB pool
# ---------------------------------------------------------------------------

def _make_artifact_row(
    slug="test-page",
    content_url=None,
    input_data=None,
    template_used=None,
    organization_id="org-123",
    campaign_id="camp-456",
):
    """Create a mock DB row dict for generated_artifacts."""
    return {
        "id": "art-789",
        "slug": slug,
        "content_url": content_url,
        "input_data": json.dumps(input_data) if isinstance(input_data, dict) else input_data,
        "template_used": template_used,
        "organization_id": organization_id,
        "campaign_id": campaign_id,
    }


# ---------------------------------------------------------------------------
# Tests: Using FastAPI TestClient
# ---------------------------------------------------------------------------

# We test the router endpoints using the ASGI test client pattern.
# All DB and external calls are mocked.

from fastapi import FastAPI
from fastapi.testclient import TestClient

def _make_app():
    """Create a minimal FastAPI app with the landing pages router."""
    app = FastAPI()
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# Tests: GET /lp/{slug} — serves HTML for valid slugs
# ---------------------------------------------------------------------------

class TestServeLandingPage:
    def test_returns_404_for_unknown_slug(self):
        app = _make_app()
        client = TestClient(app)

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            resp = client.get("/lp/nonexistent")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"

    def test_serves_html_from_content_url(self):
        app = _make_app()
        client = TestClient(app)

        artifact = _make_artifact_row(content_url="https://storage.example.com/page.html")

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get, \
             patch("src.landing_pages.router.httpx.AsyncClient") as mock_httpx_cls:
            mock_get.return_value = artifact

            # Mock httpx response
            mock_resp = MagicMock()
            mock_resp.text = "<html><body>Stored HTML</body></html>"
            mock_resp.raise_for_status = MagicMock()
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_resp)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_cls.return_value = mock_client_instance

            resp = client.get("/lp/test-page")

        assert resp.status_code == 200
        assert "Stored HTML" in resp.text

    def test_fallback_renders_from_input_data(self):
        app = _make_app()
        client = TestClient(app)

        input_data = {
            "headline": "Test Page",
            "subhead": "A great offer",
            "value_props": ["Benefit 1"],
            "form_fields": [{"name": "email", "label": "Email", "type": "email", "required": True}],
            "cta_text": "Get It",
            "branding": {
                "primary_color": "#00e87b",
                "secondary_color": "#09090b",
                "font_family": "Inter, sans-serif",
                "company_name": "TestCo",
            },
            "tracking": {"rudderstack_write_key": "", "rudderstack_data_plane_url": ""},
        }
        artifact = _make_artifact_row(
            content_url=None,
            input_data=input_data,
            template_used="lead_magnet_download",
        )

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = artifact
            resp = client.get("/lp/test-page")

        assert resp.status_code == 200
        assert "Test Page" in resp.text
        assert "<!DOCTYPE html>" in resp.text

    def test_returns_404_when_no_content_url_and_no_input_data(self):
        app = _make_app()
        client = TestClient(app)

        artifact = _make_artifact_row(content_url=None, input_data=None, template_used=None)

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = artifact
            resp = client.get("/lp/test-page")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: POST /lp/{slug}/submit — form submissions
# ---------------------------------------------------------------------------

class TestSubmitLandingPageForm:
    def test_returns_404_for_unknown_slug(self):
        app = _make_app()
        client = TestClient(app)

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            resp = client.post("/lp/nonexistent/submit", json={"email": "test@test.com"})

        assert resp.status_code == 404

    def _make_mock_pool(self):
        """Create a properly mocked asyncpg pool with async context manager support."""
        mock_conn = AsyncMock()
        mock_pool = MagicMock()

        # Create a proper async context manager for pool.acquire()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_ctx

        return mock_pool, mock_conn

    def test_successful_form_submission(self):
        app = _make_app()
        client = TestClient(app)

        artifact = _make_artifact_row()
        mock_pool, mock_conn = self._make_mock_pool()

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get, \
             patch("src.landing_pages.router.get_pool", new_callable=AsyncMock) as mock_get_pool, \
             patch("src.landing_pages.router.rudderstack") as mock_rs:
            mock_get.return_value = artifact
            mock_get_pool.return_value = mock_pool
            mock_rs.identify = AsyncMock()
            mock_rs.track = AsyncMock()

            resp = client.post(
                "/lp/test-page/submit",
                json={
                    "email": "user@example.com",
                    "name": "Jane Doe",
                    "anonymous_id": "anon-123",
                },
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify DB insert was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "INSERT INTO landing_page_submissions" in call_args[0][0]

    def test_stores_utm_params(self):
        app = _make_app()
        client = TestClient(app)

        artifact = _make_artifact_row()
        mock_pool, mock_conn = self._make_mock_pool()

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get, \
             patch("src.landing_pages.router.get_pool", new_callable=AsyncMock) as mock_get_pool, \
             patch("src.landing_pages.router.rudderstack") as mock_rs:
            mock_get.return_value = artifact
            mock_get_pool.return_value = mock_pool
            mock_rs.identify = AsyncMock()
            mock_rs.track = AsyncMock()

            resp = client.post(
                "/lp/test-page/submit",
                json={
                    "email": "user@example.com",
                    "utm_source": "linkedin",
                    "utm_medium": "cpc",
                    "utm_campaign": "spring2026",
                },
            )

        assert resp.status_code == 200

        # Check UTM params in the DB insert
        call_args = mock_conn.execute.call_args
        utm_json = call_args[0][4]  # 5th positional arg is utm_params JSON
        utm = json.loads(utm_json)
        assert utm["utm_source"] == "linkedin"
        assert utm["utm_medium"] == "cpc"
        assert utm["utm_campaign"] == "spring2026"

    def test_fires_rudderstack_events(self):
        app = _make_app()
        client = TestClient(app)

        artifact = _make_artifact_row()
        mock_pool, mock_conn = self._make_mock_pool()

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get, \
             patch("src.landing_pages.router.get_pool", new_callable=AsyncMock) as mock_get_pool, \
             patch("src.landing_pages.router.rudderstack") as mock_rs:
            mock_get.return_value = artifact
            mock_get_pool.return_value = mock_pool
            mock_rs.identify = AsyncMock()
            mock_rs.track = AsyncMock()

            resp = client.post(
                "/lp/test-page/submit",
                json={"email": "user@example.com", "anonymous_id": "anon-123"},
            )

        assert resp.status_code == 200

        # Verify identify was called (email present)
        mock_rs.identify.assert_called_once()
        identify_kwargs = mock_rs.identify.call_args[1]
        assert identify_kwargs["user_id"] == "user@example.com"
        assert identify_kwargs["anonymous_id"] == "anon-123"

        # Verify track was called
        mock_rs.track.assert_called_once()
        track_kwargs = mock_rs.track.call_args[1]
        assert track_kwargs["event"] == "form_submitted"
        assert track_kwargs["properties"]["slug"] == "test-page"

    def test_no_identify_without_email(self):
        app = _make_app()
        client = TestClient(app)

        artifact = _make_artifact_row()
        mock_pool, mock_conn = self._make_mock_pool()

        with patch("src.landing_pages.router._get_artifact_by_slug", new_callable=AsyncMock) as mock_get, \
             patch("src.landing_pages.router.get_pool", new_callable=AsyncMock) as mock_get_pool, \
             patch("src.landing_pages.router.rudderstack") as mock_rs:
            mock_get.return_value = artifact
            mock_get_pool.return_value = mock_pool
            mock_rs.identify = AsyncMock()
            mock_rs.track = AsyncMock()

            resp = client.post(
                "/lp/test-page/submit",
                json={"name": "No Email User"},
            )

        assert resp.status_code == 200

        # identify should NOT be called without email
        mock_rs.identify.assert_not_called()

        # track should still be called
        mock_rs.track.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: Endpoints are public (no auth required)
# ---------------------------------------------------------------------------

class TestLandingPagesPublic:
    def test_get_endpoint_has_no_auth_dependency(self):
        """GET /lp/{slug} should not require auth."""
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/{slug}" and "GET" in getattr(route, "methods", set()):
                # No auth dependencies in the route
                deps = getattr(route, "dependencies", [])
                assert len(deps) == 0

    def test_post_endpoint_has_no_auth_dependency(self):
        """POST /lp/{slug}/submit should not require auth."""
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/{slug}/submit" and "POST" in getattr(route, "methods", set()):
                deps = getattr(route, "dependencies", [])
                assert len(deps) == 0


# ---------------------------------------------------------------------------
# Tests: Router registered in main app
# ---------------------------------------------------------------------------

class TestRouterRegistration:
    def test_landing_pages_router_imported_in_main(self):
        """The landing pages router import is present in main.py."""
        from pathlib import Path
        main_py = Path(__file__).parent.parent / "src" / "main.py"
        source = main_py.read_text()
        assert "from src.landing_pages.router import router" in source
        assert "landing_pages_router" in source


# ---------------------------------------------------------------------------
# Tests: RudderStack integration module
# ---------------------------------------------------------------------------

class TestRudderStackIntegration:
    async def test_identify_skips_when_not_configured(self):
        with patch("src.integrations.rudderstack.settings") as mock_settings:
            mock_settings.rudderstack_write_key = ""
            mock_settings.rudderstack_data_plane_url = ""

            from src.integrations.rudderstack import identify
            # Should not raise, just skip
            await identify("anon-1", "user@test.com", {"email": "user@test.com"})

    async def test_track_skips_when_not_configured(self):
        with patch("src.integrations.rudderstack.settings") as mock_settings:
            mock_settings.rudderstack_write_key = ""
            mock_settings.rudderstack_data_plane_url = ""

            from src.integrations.rudderstack import track
            await track("anon-1", "user@test.com", "test_event", {"key": "val"})

    async def test_identify_calls_rudderstack_api(self):
        with patch("src.integrations.rudderstack.settings") as mock_settings, \
             patch("src.integrations.rudderstack.httpx.AsyncClient") as mock_httpx_cls:
            mock_settings.rudderstack_write_key = "test-key"
            mock_settings.rudderstack_data_plane_url = "https://rs.example.com"

            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_cls.return_value = mock_client

            from src.integrations.rudderstack import identify
            await identify("anon-1", "user@test.com", {"email": "user@test.com"})

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "v1/identify" in call_args[0][0]

    async def test_track_calls_rudderstack_api(self):
        with patch("src.integrations.rudderstack.settings") as mock_settings, \
             patch("src.integrations.rudderstack.httpx.AsyncClient") as mock_httpx_cls:
            mock_settings.rudderstack_write_key = "test-key"
            mock_settings.rudderstack_data_plane_url = "https://rs.example.com"

            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_cls.return_value = mock_client

            from src.integrations.rudderstack import track
            await track("anon-1", "user@test.com", "form_submitted", {"slug": "test"})

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "v1/track" in call_args[0][0]

    async def test_identify_handles_api_error_gracefully(self):
        with patch("src.integrations.rudderstack.settings") as mock_settings, \
             patch("src.integrations.rudderstack.httpx.AsyncClient") as mock_httpx_cls:
            mock_settings.rudderstack_write_key = "test-key"
            mock_settings.rudderstack_data_plane_url = "https://rs.example.com"

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Connection error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_httpx_cls.return_value = mock_client

            from src.integrations.rudderstack import identify
            # Should not raise
            await identify("anon-1", "user@test.com", {"email": "user@test.com"})
