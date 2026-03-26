from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.routing.registry import RouteRegistry, registry
from src.shared.errors import UnknownRouteError
from src.specs.loader import SpecLoader


SPECS_DIR = Path(__file__).parent.parent / "src" / "specs"


@pytest.fixture(autouse=True)
def load_specs():
    """Load specs into the global registry for all tests."""
    specs = SpecLoader.load_all(SPECS_DIR)
    registry.register(specs)
    yield


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestRouteRegistry:
    def test_resolve_known_route(self):
        spec = registry.resolve("structured_text", "linkedin")
        assert spec.spec_id == "structured_text__linkedin"

    def test_resolve_unknown_route_raises(self):
        with pytest.raises(UnknownRouteError):
            registry.resolve("unknown", "unknown")

    def test_unknown_route_includes_available(self):
        try:
            registry.resolve("unknown", "unknown")
        except UnknownRouteError as e:
            assert len(e.available) > 0

    def test_list_routes(self):
        routes = registry.list_routes()
        assert len(routes) >= 12


class TestGenerateEndpoint:
    def test_sync_generate_returns_completed(self, client):
        response = client.post(
            "/generate",
            json={
                "artifact_type": "structured_text",
                "surface": "linkedin",
                "content_props": {"headline": "Test"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["artifact_type"] == "structured_text"
        assert data["spec_id"] == "structured_text__linkedin"
        assert "artifact_id" in data

    def test_async_generate_returns_queued(self, client):
        response = client.post(
            "/generate",
            json={
                "artifact_type": "video",
                "surface": "generic",
                "content_props": {"concept": "Test video"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "job_id" in data
        assert "poll_url" in data

    def test_unknown_route_returns_422(self, client):
        response = client.post(
            "/generate",
            json={
                "artifact_type": "nonexistent",
                "surface": "nowhere",
                "content_props": {},
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "unknown_route"


class TestBatchEndpoint:
    def test_batch_generate(self, client):
        response = client.post(
            "/generate/batch",
            json={
                "items": [
                    {
                        "artifact_type": "structured_text",
                        "surface": "linkedin",
                        "content_props": {"headline": "Test 1"},
                    },
                    {
                        "artifact_type": "structured_text",
                        "surface": "meta",
                        "content_props": {"primary_text": "Test 2"},
                    },
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_batch_with_errors(self, client):
        response = client.post(
            "/generate/batch",
            json={
                "items": [
                    {
                        "artifact_type": "structured_text",
                        "surface": "linkedin",
                        "content_props": {},
                    },
                    {
                        "artifact_type": "nonexistent",
                        "surface": "nowhere",
                        "content_props": {},
                    },
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert len(data["errors"]) == 1


class TestJobEndpoint:
    def test_get_job_returns_error_without_db(self, client):
        """Without a DB pool, the jobs endpoint returns 500."""
        response = client.get("/jobs/fake-job-id")
        # No DB pool in test context, so this returns 500
        assert response.status_code == 500
