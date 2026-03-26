import time
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from jose import jwt

from src.auth.middleware import AuthMiddleware, RateLimitMiddleware, PUBLIC_PREFIXES
from src.auth.models import APIKeyRecord, Organization
from src.auth.service import verify_api_key, verify_jwt, resolve_organization
from src.shared.errors import AuthenticationError, RateLimitExceededError


# --- Service tests ---

class TestVerifyJWT:
    def test_valid_jwt(self):
        secret = "test-secret"
        token = jwt.encode({"organization_id": "org-123"}, secret, algorithm="HS256")
        with patch("src.auth.service.settings") as mock_settings:
            mock_settings.jwt_secret = secret
            claims = verify_jwt(token)
        assert claims["organization_id"] == "org-123"

    def test_invalid_jwt(self):
        with patch("src.auth.service.settings") as mock_settings:
            mock_settings.jwt_secret = "secret"
            with pytest.raises(AuthenticationError, match="Invalid JWT"):
                verify_jwt("bad.token.here")

    def test_missing_org_id_claim(self):
        secret = "test-secret"
        token = jwt.encode({"sub": "user-1"}, secret, algorithm="HS256")
        with patch("src.auth.service.settings") as mock_settings:
            mock_settings.jwt_secret = secret
            with pytest.raises(AuthenticationError, match="missing organization_id"):
                verify_jwt(token)

    def test_no_jwt_secret_configured(self):
        with patch("src.auth.service.settings") as mock_settings:
            mock_settings.jwt_secret = ""
            with pytest.raises(AuthenticationError, match="not configured"):
                verify_jwt("any.token.here")


class TestVerifyAPIKey:
    async def test_valid_api_key(self):
        raw_key = "cex_live_test1234"
        hashed = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
        mock_row = {
            "id": "key-1",
            "organization_id": "org-1",
            "key_hash": hashed,
            "key_prefix": "cex_live",
            "name": "test",
            "scopes": [],
            "rate_limit_rpm": 60,
            "is_active": True,
            "last_used_at": None,
            "created_at": None,
            "expires_at": None,
        }
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)
        mock_conn.execute = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        record = await verify_api_key(raw_key, mock_pool)
        assert record.organization_id == "org-1"

    async def test_invalid_api_key_not_found(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            await verify_api_key("bad_key", mock_pool)


class TestResolveOrganization:
    async def test_found(self):
        mock_row = {
            "id": "org-1",
            "name": "Test Org",
            "slug": "test-org",
            "created_at": None,
            "updated_at": None,
        }
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        org = await resolve_organization("org-1", mock_pool)
        assert org.name == "Test Org"

    async def test_not_found(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(AuthenticationError, match="Organization not found"):
            await resolve_organization("org-999", mock_pool)


# --- Middleware tests ---

class TestPublicPrefixes:
    def test_health_is_public(self):
        assert any("/health".startswith(p) for p in PUBLIC_PREFIXES)

    def test_lp_is_public(self):
        assert any("/lp/some-slug".startswith(p) for p in PUBLIC_PREFIXES)


class TestRateLimitMiddleware:
    async def test_allows_under_limit(self):
        app_mock = MagicMock()
        middleware = RateLimitMiddleware(app_mock)

        request = MagicMock()
        request.state = MagicMock()
        request.state.api_key_id = "key-1"
        request.state.rate_limit_rpm = 5

        call_next = AsyncMock(return_value="ok")
        result = await middleware.dispatch(request, call_next)
        assert result == "ok"

    async def test_blocks_over_limit(self):
        app_mock = MagicMock()
        middleware = RateLimitMiddleware(app_mock)

        request = MagicMock()
        request.state = MagicMock()
        request.state.api_key_id = "key-2"
        request.state.rate_limit_rpm = 2

        call_next = AsyncMock(return_value="ok")

        # Fill up the limit
        middleware._requests["key-2"] = [time.time(), time.time()]

        with pytest.raises(RateLimitExceededError):
            await middleware.dispatch(request, call_next)

    async def test_skips_when_no_api_key(self):
        app_mock = MagicMock()
        middleware = RateLimitMiddleware(app_mock)

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no api_key_id attr

        call_next = AsyncMock(return_value="ok")
        result = await middleware.dispatch(request, call_next)
        assert result == "ok"
