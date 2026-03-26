"""RudderStack server-side analytics integration.

CEX-28: Provides identify() and track() helpers for server-side event firing.
Used by the landing page form submission flow.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


async def identify(
    anonymous_id: str,
    user_id: str,
    traits: dict[str, Any],
) -> None:
    """Server-side RudderStack identify() — merge anonymous -> known identity."""
    if not settings.rudderstack_data_plane_url or not settings.rudderstack_write_key:
        logger.debug("RudderStack not configured — skipping identify")
        return

    payload = {
        "anonymousId": anonymous_id,
        "userId": user_id,
        "traits": traits,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.rudderstack_data_plane_url}/v1/identify",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {settings.rudderstack_write_key}",
                },
                timeout=5.0,
            )
            resp.raise_for_status()
    except Exception:
        logger.exception("RudderStack identify failed")


async def track(
    anonymous_id: str,
    user_id: str,
    event: str,
    properties: dict[str, Any],
) -> None:
    """Server-side RudderStack track() — fire event."""
    if not settings.rudderstack_data_plane_url or not settings.rudderstack_write_key:
        logger.debug("RudderStack not configured — skipping track")
        return

    payload = {
        "anonymousId": anonymous_id,
        "userId": user_id,
        "event": event,
        "properties": properties,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.rudderstack_data_plane_url}/v1/track",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {settings.rudderstack_write_key}",
                },
                timeout=5.0,
            )
            resp.raise_for_status()
    except Exception:
        logger.exception("RudderStack track failed")
