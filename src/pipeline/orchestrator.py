"""Pipeline orchestrator — wires Generator → Renderer → Storage → DB.

Handles both sync (return immediately) and async (create job, run in background) flows.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from src.brand.models import BrandContext
from src.brand.service import build_brand_context
from src.db import get_pool
from src.integrations.claude_client import ClaudeClient
from src.integrations.supabase_client import SupabaseClient
from src.jobs.service import JobService
from src.pipeline.registry import resolve_generator, resolve_renderer
from src.specs.models import FormatSpec
from src.storage.service import StorageService

logger = logging.getLogger(__name__)


async def run_sync_pipeline(
    spec: FormatSpec,
    content_props: dict,
    brand_context: BrandContext,
    org_id: str,
    subtype: str | None = None,
) -> dict:
    """Run the full sync generation pipeline and return the result.

    Flow: resolve classes → generate content → render (if needed) → store → insert DB row → return.
    """
    artifact_id = str(uuid.uuid4())

    # 1. Resolve pipeline classes
    generator_cls = resolve_generator(spec.artifact_type, spec.surface, subtype)
    renderer_cls = resolve_renderer(spec.artifact_type, spec.surface)

    # 2. Instantiate services
    claude_client = ClaudeClient()
    generator = generator_cls()

    # 3. Generate content via Claude
    generated = await generator.generate(
        content_props=content_props,
        brand_context=brand_context,
        spec=spec,
        claude_client=claude_client,
    )

    # 4. Render if needed
    content_url = None
    content_json = None
    slug = None
    template_used = subtype

    if renderer_cls is not None:
        renderer = renderer_cls()
        rendered = await renderer.render(
            content=generated,
            spec=spec,
            brand_context=brand_context,
        )

        # 5. Upload to storage
        supabase = SupabaseClient()
        storage = StorageService(supabase)
        content_url = await storage.upload_artifact(
            org_id=org_id,
            artifact_type=spec.artifact_type,
            artifact_id=artifact_id,
            data=rendered.data,
            content_type=rendered.content_type,
        )

        # For landing pages, generate a slug
        if spec.artifact_type == "html_page":
            slug = uuid.uuid4().hex[:12]
    else:
        # JSON-only output (structured_text, physical_mail)
        if hasattr(generated, "content"):
            raw = generated.content
            if hasattr(raw, "model_dump"):
                content_json = raw.model_dump(mode="json")
            elif isinstance(raw, dict):
                content_json = raw
            else:
                content_json = {"result": str(raw)}
        else:
            content_json = {"result": str(generated)}

    # 6. Insert artifact record into DB
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO generated_artifacts
               (id, organization_id, artifact_type, surface, subtype, spec_id,
                status, content_url, content_json, slug, template_used,
                input_data, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, $12::jsonb, $13, $13)""",
            artifact_id,
            org_id,
            spec.artifact_type,
            spec.surface,
            subtype,
            spec.spec_id,
            "completed",
            content_url,
            json.dumps(content_json) if content_json else None,
            slug,
            template_used,
            json.dumps(content_props),
            now,
        )

    # Build content preview
    content_preview = None
    if content_json:
        from src.shared.text import truncate_at_word_boundary
        preview_str = json.dumps(content_json)
        content_preview = truncate_at_word_boundary(preview_str, 500)
    elif content_url:
        content_preview = f"Artifact stored at {content_url}"

    return {
        "artifact_id": artifact_id,
        "artifact_type": spec.artifact_type,
        "surface": spec.surface,
        "status": "completed",
        "content_url": content_url,
        "content": content_json,
        "content_preview": content_preview,
        "spec_id": spec.spec_id,
        "created_at": now,
        "slug": slug,
    }


async def run_async_pipeline(
    spec: FormatSpec,
    content_props: dict,
    brand_context: BrandContext,
    org_id: str,
    subtype: str | None = None,
    webhook_url: str | None = None,
    callback_metadata: dict | None = None,
) -> dict:
    """Create a job and kick off async generation in a background task.

    Returns the job info immediately. The actual pipeline runs via execute_async_job().
    """
    pool = await get_pool()
    job_service = JobService(pool)

    job = await job_service.create_job(
        organization_id=org_id,
        artifact_type=spec.artifact_type,
        surface=spec.surface,
        input_data={
            "content_props": content_props,
            "brand_context": brand_context.model_dump(mode="json"),
            "spec_id": spec.spec_id,
            "subtype": subtype,
        },
        webhook_url=webhook_url,
        callback_metadata=callback_metadata,
    )

    return {
        "job_id": job.id,
        "artifact_type": spec.artifact_type,
        "surface": spec.surface,
        "status": "queued",
        "poll_url": f"/jobs/{job.id}",
        "webhook_url": webhook_url,
    }


async def execute_async_job(job_id: str) -> None:
    """Execute an async generation job (called as a background task).

    Runs the full pipeline: generate → render → store → update job status.
    """
    pool = await get_pool()
    job_service = JobService(pool)

    try:
        job = await job_service.get_job(job_id)
        input_data = job.input_data or {}

        await job_service.update_status(job_id, status="rendering", progress=0.1)

        # Reconstruct pipeline inputs from stored job data
        content_props = input_data.get("content_props", {})
        brand_data = input_data.get("brand_context", {})
        brand_context = BrandContext(**brand_data)
        subtype = input_data.get("subtype")
        spec_id = input_data.get("spec_id", "")

        # Resolve spec from registry
        from src.routing.registry import registry
        spec = registry.resolve(job.artifact_type, job.surface)

        artifact_id = str(uuid.uuid4())
        generator_cls = resolve_generator(spec.artifact_type, spec.surface, subtype)
        renderer_cls = resolve_renderer(spec.artifact_type, spec.surface)

        claude_client = ClaudeClient()
        generator = generator_cls()

        await job_service.update_status(job_id, status="rendering", progress=0.2)

        # Generate
        generated = await generator.generate(
            content_props=content_props,
            brand_context=brand_context,
            spec=spec,
            claude_client=claude_client,
        )

        await job_service.update_status(job_id, status="rendering", progress=0.5)

        # Render
        content_url = None
        if renderer_cls is not None:
            renderer = renderer_cls()

            # For audio/video renderers with render_pipeline, use that instead
            if hasattr(renderer, "render_pipeline"):
                rendered = await renderer.render_pipeline(
                    content=generated,
                    spec=spec,
                    brand_context=brand_context,
                    job_id=job_id,
                    job_service=job_service,
                    org_id=job.organization_id,
                    artifact_id=artifact_id,
                )
                if hasattr(rendered, "metadata") and rendered.metadata:
                    content_url = rendered.metadata.get("content_url")
            else:
                rendered = await renderer.render(
                    content=generated,
                    spec=spec,
                    brand_context=brand_context,
                )
                # Upload
                supabase = SupabaseClient()
                storage = StorageService(supabase)
                content_url = await storage.upload_artifact(
                    org_id=job.organization_id,
                    artifact_type=spec.artifact_type,
                    artifact_id=artifact_id,
                    data=rendered.data,
                    content_type=rendered.content_type,
                )

        await job_service.update_status(
            job_id, status="rendering", progress=0.9, artifact_id=artifact_id
        )

        # Insert artifact record (match sync pipeline's column set for schema parity)
        now = datetime.now(timezone.utc)
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO generated_artifacts
                   (id, organization_id, artifact_type, surface, subtype, spec_id,
                    status, content_url, content_json, slug, template_used,
                    input_data, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, $12::jsonb, $13, $13)""",
                artifact_id,
                job.organization_id,
                spec.artifact_type,
                spec.surface,
                subtype,
                spec.spec_id,
                "completed",
                content_url,
                None,  # content_json — async artifacts are file-based
                None,  # slug
                subtype,  # template_used
                json.dumps(content_props),
                now,
            )

        await job_service.complete_job(job_id, artifact_id, content_url=content_url)

    except Exception as e:
        logger.exception(f"Async job {job_id} failed: {e}")
        try:
            await job_service.fail_job(job_id, str(e))
        except Exception:
            logger.exception(f"Failed to mark job {job_id} as failed")
