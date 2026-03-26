import json
import logging
from datetime import datetime, timezone

import httpx

from src.jobs.models import Job, WebhookPayload
from src.shared.errors import JobNotFoundError
from src.shared.models import ErrorDetail

logger = logging.getLogger(__name__)

# Sync artifact types return immediately; async types create jobs
SYNC_ARTIFACT_TYPES = {
    "structured_text",
    "pdf",
    "html_page",
    "document_slides",
    "image",
    "physical_mail",
}
ASYNC_ARTIFACT_TYPES = {"video", "audio"}


class JobService:
    def __init__(self, pool):
        self._pool = pool

    async def create_job(
        self,
        organization_id: str,
        artifact_type: str,
        surface: str,
        input_data: dict,
        webhook_url: str | None = None,
        callback_metadata: dict | None = None,
    ) -> Job:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO jobs (organization_id, artifact_type, surface, input_data, webhook_url, callback_metadata)
                   VALUES ($1, $2, $3, $4::jsonb, $5, $6::jsonb)
                   RETURNING *""",
                organization_id,
                artifact_type,
                surface,
                json.dumps(input_data),
                webhook_url,
                json.dumps(callback_metadata) if callback_metadata else None,
            )
        return self._row_to_job(row)

    async def get_job(self, job_id: str) -> Job:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
        if row is None:
            raise JobNotFoundError(job_id)
        return self._row_to_job(row)

    async def update_status(
        self,
        job_id: str,
        status: str,
        progress: float | None = None,
        artifact_id: str | None = None,
        error_message: str | None = None,
        provider_job_id: str | None = None,
    ) -> Job:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE jobs SET
                    status = $2,
                    progress = COALESCE($3, progress),
                    artifact_id = COALESCE($4, artifact_id),
                    error_message = COALESCE($5, error_message),
                    provider_job_id = COALESCE($6, provider_job_id),
                    updated_at = now(),
                    completed_at = CASE WHEN $2 IN ('completed', 'failed') THEN now() ELSE completed_at END
                   WHERE id = $1
                   RETURNING *""",
                job_id,
                status,
                progress,
                artifact_id,
                error_message,
                provider_job_id,
            )
        if row is None:
            raise JobNotFoundError(job_id)
        return self._row_to_job(row)

    async def complete_job(
        self, job_id: str, artifact_id: str, content_url: str | None = None
    ) -> Job:
        job = await self.update_status(
            job_id, status="completed", artifact_id=artifact_id, progress=1.0
        )
        if job.webhook_url:
            await self._send_webhook(job, content_url=content_url)
        return job

    async def fail_job(self, job_id: str, error_message: str) -> Job:
        job = await self.update_status(
            job_id, status="failed", error_message=error_message
        )
        if job.webhook_url:
            await self._send_webhook(job)
        return job

    async def _send_webhook(self, job: Job, content_url: str | None = None) -> None:
        if not job.webhook_url:
            return
        payload = WebhookPayload(
            event="job.completed" if job.status == "completed" else "job.failed",
            job_id=job.id,
            artifact_id=job.artifact_id,
            artifact_type=job.artifact_type,
            surface=job.surface,
            status=job.status,
            content_url=content_url,
            error=ErrorDetail(code="job_failed", message=job.error_message or "")
            if job.status == "failed"
            else None,
            callback_metadata=job.callback_metadata,
            timestamp=datetime.now(timezone.utc),
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    job.webhook_url,
                    json=payload.model_dump(mode="json"),
                )
        except Exception as e:
            logger.error(f"Webhook delivery failed for job {job.id}: {e}")

    @staticmethod
    def _row_to_job(row) -> Job:
        data = dict(row)
        # Convert UUID to str
        for key in ("id", "organization_id", "artifact_id"):
            if data.get(key) is not None:
                data[key] = str(data[key])
        # Parse JSON fields
        if isinstance(data.get("input_data"), str):
            data["input_data"] = json.loads(data["input_data"])
        if isinstance(data.get("callback_metadata"), str):
            data["callback_metadata"] = json.loads(data["callback_metadata"])
        return Job(**data)
