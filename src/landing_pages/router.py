"""Landing page hosting + form handling.

CEX-28: Public endpoints (no auth):
- GET  /lp/{slug} — serve generated HTML with RudderStack JS SDK injected
- POST /lp/{slug}/submit — handle form submission, fire RudderStack identify + track

Ported from paid-engine-x app/landing_pages/router.py.
Uses asyncpg (from src.db) instead of Supabase client for DB queries.
Uses generated_artifacts table (not generated_assets).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.db import get_pool
from src.integrations import rudderstack
from src.providers.jinja2_provider import get_jinja2_env

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lp", tags=["landing_pages"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_artifact_by_slug(slug: str) -> dict | None:
    """Look up a landing page / case study page by slug using asyncpg."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, organization_id, campaign_id, content_url, input_data,
                   template_used, slug
            FROM generated_artifacts
            WHERE slug = $1
            """,
            slug,
        )
    if row is None:
        return None
    return dict(row)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{slug}", response_class=HTMLResponse)
async def serve_landing_page(slug: str, request: Request):
    """Serve a published landing page by its slug (public, no auth)."""
    artifact = await _get_artifact_by_slug(slug)
    if artifact is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": "Landing page not found"}},
        )

    content_url = artifact.get("content_url")

    if content_url:
        # Fetch rendered HTML from Supabase Storage
        async with httpx.AsyncClient() as client:
            resp = await client.get(content_url)
            resp.raise_for_status()
        return HTMLResponse(content=resp.text, status_code=200)

    # Fallback: render from input_data using Jinja2 templates
    input_data = artifact.get("input_data")
    template_used = artifact.get("template_used")
    if input_data and template_used:
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        env = get_jinja2_env()
        template = env.get_template(f"{template_used}.html")
        html = template.render(slug=slug, **input_data)
        return HTMLResponse(content=html, status_code=200)

    return JSONResponse(
        status_code=404,
        content={"error": {"code": "not_found", "message": "Landing page content not available"}},
    )


@router.post("/{slug}/submit")
async def submit_landing_page_form(slug: str, request: Request):
    """Handle form submission from a landing page (public, no auth).

    - Stores submission in landing_page_submissions
    - Captures UTM parameters
    - Fires RudderStack identify() to merge anonymous -> known identity
    - Fires RudderStack track() for form_submitted event
    """
    artifact = await _get_artifact_by_slug(slug)
    if artifact is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": "Landing page not found"}},
        )

    body = await request.json()

    # Extract known fields
    email = body.get("email", "")
    anonymous_id = body.get("anonymous_id", "") or body.get("anonymousId", "")

    # Extract UTM parameters
    utm_params = {
        k: body.get(k, "")
        for k in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")
        if body.get(k)
    }

    submitted_at = datetime.now(UTC).isoformat()

    # Store in landing_page_submissions via asyncpg
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO landing_page_submissions
                (artifact_id, slug, form_data, utm_params, organization_id, campaign_id, submitted_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            str(artifact["id"]),
            slug,
            json.dumps(body),
            json.dumps(utm_params),
            artifact.get("organization_id"),
            artifact.get("campaign_id"),
            submitted_at,
        )

    # Fire RudderStack identify — merge anonymous visitor to known identity
    if email:
        traits = {k: v for k, v in body.items() if k not in ("anonymous_id", "anonymousId")}
        traits["email"] = email
        await rudderstack.identify(
            anonymous_id=anonymous_id or email,
            user_id=email,
            traits=traits,
        )

    # Fire RudderStack track — form_submitted event
    track_properties = {
        "slug": slug,
        "template": artifact.get("template_used", ""),
        "campaign_id": artifact.get("campaign_id", ""),
        "organization_id": artifact.get("organization_id", ""),
        **utm_params,
    }
    await rudderstack.track(
        anonymous_id=anonymous_id or email or "unknown",
        user_id=email or "",
        event="form_submitted",
        properties=track_properties,
    )

    return JSONResponse(
        content={"status": "ok", "message": "Form submitted successfully"},
        status_code=200,
    )
