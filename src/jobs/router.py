from typing import Any

from fastapi import APIRouter

from src.db import get_pool
from src.jobs.service import JobService
from src.routing.router import JobStatusResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> Any:
    pool = await get_pool()
    service = JobService(pool)
    job = await service.get_job(job_id)
    return JobStatusResponse(
        job_id=job.id,
        artifact_id=job.artifact_id,
        status=job.status,
        progress=job.progress,
        content_url=None,
        error=None,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
