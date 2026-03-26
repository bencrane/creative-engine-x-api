from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.shared.models import ErrorDetail


class Job(BaseModel):
    id: str
    organization_id: str
    artifact_id: str | None = None
    artifact_type: str
    surface: str
    status: Literal["queued", "rendering", "completed", "failed"] = "queued"
    progress: float | None = None
    input_data: dict = {}
    webhook_url: str | None = None
    callback_metadata: dict | None = None
    error_message: str | None = None
    provider_job_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class WebhookPayload(BaseModel):
    event: Literal["job.completed", "job.failed"]
    job_id: str
    artifact_id: str | None = None
    artifact_type: str
    surface: str
    status: str
    content_url: str | None = None
    error: ErrorDetail | None = None
    callback_metadata: dict | None = None
    timestamp: datetime
