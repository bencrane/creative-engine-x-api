import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.jobs.models import Job, WebhookPayload
from src.jobs.service import JobService, SYNC_ARTIFACT_TYPES, ASYNC_ARTIFACT_TYPES
from src.shared.errors import JobNotFoundError


def _make_job_row(**overrides):
    defaults = {
        "id": str(uuid.uuid4()),
        "organization_id": str(uuid.uuid4()),
        "artifact_id": None,
        "artifact_type": "video",
        "surface": "generic",
        "status": "queued",
        "progress": None,
        "input_data": json.dumps({"test": True}),
        "webhook_url": None,
        "callback_metadata": None,
        "error_message": None,
        "provider_job_id": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    defaults.update(overrides)
    return defaults


class TestJobModels:
    def test_job_defaults(self):
        job = Job(
            id="j-1",
            organization_id="org-1",
            artifact_type="video",
            surface="generic",
        )
        assert job.status == "queued"
        assert job.progress is None

    def test_webhook_payload(self):
        payload = WebhookPayload(
            event="job.completed",
            job_id="j-1",
            artifact_type="video",
            surface="generic",
            status="completed",
            timestamp=datetime.now(timezone.utc),
        )
        assert payload.event == "job.completed"


class TestJobService:
    async def test_create_job(self):
        row = _make_job_row()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        job = await service.create_job(
            organization_id="org-1",
            artifact_type="video",
            surface="generic",
            input_data={"test": True},
        )
        assert isinstance(job, Job)
        assert job.artifact_type == "video"

    async def test_get_job(self):
        row = _make_job_row()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        job = await service.get_job(row["id"])
        assert job.id == row["id"]

    async def test_get_job_not_found(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        with pytest.raises(JobNotFoundError):
            await service.get_job("nonexistent")

    async def test_update_status(self):
        row = _make_job_row(status="rendering", progress=0.5)
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        job = await service.update_status(row["id"], status="rendering", progress=0.5)
        assert job.status == "rendering"
        assert job.progress == 0.5

    async def test_complete_job(self):
        row = _make_job_row(status="completed", progress=1.0)
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        job = await service.complete_job(row["id"], artifact_id="art-1")
        assert job.status == "completed"

    async def test_fail_job(self):
        row = _make_job_row(status="failed", error_message="Something broke")
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        job = await service.fail_job(row["id"], error_message="Something broke")
        assert job.status == "failed"

    @patch("src.jobs.service.httpx.AsyncClient")
    async def test_webhook_delivery_on_complete(self, mock_httpx_class):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock()
        mock_httpx_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_httpx_class.return_value.__aexit__ = AsyncMock(return_value=False)

        row = _make_job_row(
            status="completed",
            progress=1.0,
            webhook_url="https://example.com/webhook",
        )
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        service = JobService(mock_pool)
        await service.complete_job(row["id"], artifact_id="art-1")
        mock_client.post.assert_awaited_once()


class TestArtifactTypeClassification:
    def test_sync_types(self):
        for t in ["structured_text", "pdf", "html_page", "document_slides", "image", "physical_mail"]:
            assert t in SYNC_ARTIFACT_TYPES

    def test_async_types(self):
        for t in ["video", "audio"]:
            assert t in ASYNC_ARTIFACT_TYPES
