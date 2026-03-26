"""Dependency injection stubs — filled in by later issues."""

from fastapi import Request


async def get_current_organization(request: Request) -> dict:
    """Returns the authenticated organization from request state."""
    return getattr(request.state, "organization", {})
