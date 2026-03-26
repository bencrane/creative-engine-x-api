from datetime import datetime, timezone

import bcrypt
from jose import JWTError, jwt

from src.auth.models import APIKeyRecord, Organization
from src.config import settings
from src.shared.errors import AuthenticationError


async def verify_api_key(key: str, pool) -> APIKeyRecord:
    """Verify an API key against the database. Returns the key record."""
    prefix = key[:8] if len(key) >= 8 else key
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM api_keys WHERE key_prefix = $1 AND is_active = true",
            prefix,
        )
    if row is None:
        raise AuthenticationError("Invalid API key")

    if not bcrypt.checkpw(key.encode(), row["key_hash"].encode()):
        raise AuthenticationError("Invalid API key")

    if row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc):
        raise AuthenticationError("API key expired")

    # Update last_used_at (fire and forget)
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE api_keys SET last_used_at = now() WHERE id = $1", row["id"]
        )

    return APIKeyRecord(**dict(row))


def verify_jwt(token: str) -> dict:
    """Verify a JWT and return the claims."""
    if not settings.jwt_secret:
        raise AuthenticationError("JWT authentication not configured")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError as e:
        raise AuthenticationError(f"Invalid JWT: {e}")
    if "organization_id" not in payload:
        raise AuthenticationError("JWT missing organization_id claim")
    return payload


async def resolve_organization(org_id: str, pool) -> Organization:
    """Load an organization from the database."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM organizations WHERE id = $1", org_id
        )
    if row is None:
        raise AuthenticationError(f"Organization not found: {org_id}")
    return Organization(**dict(row))
