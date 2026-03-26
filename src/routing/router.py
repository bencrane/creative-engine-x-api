import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.routing.registry import registry
from src.shared.models import ErrorDetail

router = APIRouter()


# --- Request/Response models ---

class GenerateRequest(BaseModel):
    artifact_type: str
    surface: str
    subtype: str | None = None
    content_props: dict
    brand_context_id: str | None = None
    brand_context: dict | None = None
    format_overrides: dict | None = None
    claude_model_override: str | None = None
    temperature_override: float | None = None
    idempotency_key: str | None = None
    webhook_url: str | None = None
    callback_metadata: dict | None = None


class GenerateResponse(BaseModel):
    artifact_id: str
    artifact_type: str
    surface: str
    status: Literal["completed", "failed"]
    content_url: str | None = None
    content: dict | None = None
    content_preview: str | None = None
    spec_id: str
    created_at: datetime
    error: ErrorDetail | None = None


class AsyncGenerateResponse(BaseModel):
    job_id: str
    artifact_type: str
    surface: str
    status: Literal["queued", "rendering"]
    poll_url: str
    estimated_duration_seconds: int | None = None
    webhook_url: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    artifact_id: str | None = None
    status: Literal["queued", "rendering", "completed", "failed"]
    progress: float | None = None
    content_url: str | None = None
    error: ErrorDetail | None = None
    created_at: datetime
    updated_at: datetime


class BatchGenerateRequest(BaseModel):
    items: list[GenerateRequest]
    brand_context_id: str | None = None
    brand_context: dict | None = None


class BatchItemError(BaseModel):
    index: int
    error: ErrorDetail


class BatchGenerateResponse(BaseModel):
    results: list[GenerateResponse | AsyncGenerateResponse]
    errors: list[BatchItemError] | None = None


# --- Endpoints ---

ASYNC_ARTIFACT_TYPES = {"video", "audio"}


@router.post("/generate", response_model=GenerateResponse | AsyncGenerateResponse)
async def generate(body: GenerateRequest, request: Request) -> Any:
    spec = registry.resolve(body.artifact_type, body.surface)

    is_async = (
        spec.delivery and spec.delivery.mode == "async"
    ) or body.artifact_type in ASYNC_ARTIFACT_TYPES

    if is_async:
        job_id = str(uuid.uuid4())
        return AsyncGenerateResponse(
            job_id=job_id,
            artifact_type=body.artifact_type,
            surface=body.surface,
            status="queued",
            poll_url=f"/jobs/{job_id}",
            webhook_url=body.webhook_url,
        )

    # Sync placeholder response (actual generation is Phase 2)
    artifact_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    return GenerateResponse(
        artifact_id=artifact_id,
        artifact_type=body.artifact_type,
        surface=body.surface,
        status="completed",
        content={"placeholder": True, "spec_id": spec.spec_id},
        content_preview="Placeholder response — generation not yet implemented",
        spec_id=spec.spec_id,
        created_at=now,
    )


@router.post("/generate/batch", response_model=BatchGenerateResponse)
async def generate_batch(body: BatchGenerateRequest, request: Request) -> Any:
    results: list[GenerateResponse | AsyncGenerateResponse] = []
    errors: list[BatchItemError] = []

    for i, item in enumerate(body.items[:10]):  # Max 10 per batch
        try:
            # Apply shared brand context if not overridden per item
            if item.brand_context_id is None and body.brand_context_id:
                item.brand_context_id = body.brand_context_id
            if item.brand_context is None and body.brand_context:
                item.brand_context = body.brand_context

            result = await generate(item, request)
            results.append(result)
        except Exception as e:
            errors.append(
                BatchItemError(
                    index=i,
                    error=ErrorDetail(code="generation_error", message=str(e)),
                )
            )

    return BatchGenerateResponse(
        results=results,
        errors=errors if errors else None,
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> Any:
    # Placeholder — real implementation in CEX-9
    from src.shared.errors import JobNotFoundError

    raise JobNotFoundError(job_id)
