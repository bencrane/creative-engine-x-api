import hashlib
import secrets
import uuid
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

    # Pre-hash with SHA256 to stay within bcrypt's 72-byte limit
    key_digest = hashlib.sha256(key.encode()).hexdigest().encode()
    if not bcrypt.checkpw(key_digest, row["key_hash"].encode()):
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


async def create_api_key(
    org_id: str,
    name: str,
    scopes: list[str],
    rate_limit_rpm: int,
    pool,
) -> tuple[str, APIKeyRecord]:
    """Create a new API key. Returns (raw_key, record). The raw key is only visible once."""
    raw_key = f"cex_live_{secrets.token_hex(32)}"
    # Pre-hash with SHA256 to stay within bcrypt's 72-byte limit
    key_digest = hashlib.sha256(raw_key.encode()).hexdigest().encode()
    key_hash = bcrypt.hashpw(key_digest, bcrypt.gensalt()).decode()
    key_prefix = raw_key[:8]
    key_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO api_keys (id, organization_id, key_hash, key_prefix, name, scopes, rate_limit_rpm, is_active)
               VALUES ($1, $2, $3, $4, $5, $6, $7, true)
               RETURNING *""",
            key_id,
            org_id,
            key_hash,
            key_prefix,
            name,
            scopes,
            rate_limit_rpm,
        )

    return raw_key, APIKeyRecord(**dict(row))


async def revoke_api_key(key_id: str, pool) -> None:
    """Revoke an API key by setting is_active=False."""
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE api_keys SET is_active = false WHERE id = $1", key_id
        )
    if result == "UPDATE 0":
        raise AuthenticationError(f"API key not found: {key_id}")
