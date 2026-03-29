import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.auth.service import resolve_organization, verify_api_key, verify_jwt
from src.db import get_pool
from src.shared.errors import AuthenticationError, RateLimitExceededError

PUBLIC_PREFIXES = ("/health", "/lp/", "/docs", "/openapi.json")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip auth for public routes
        if any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        try:
            pool = await get_pool()
        except RuntimeError:
            response = JSONResponse(
                {"error": "service_unavailable", "message": "Database not ready"},
                status_code=503,
            )
            return response

        api_key_header = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization")

        if api_key_header:
            key_record = await verify_api_key(api_key_header, pool)
            request.state.organization_id = key_record.organization_id
            request.state.api_key_id = key_record.id
            request.state.rate_limit_rpm = key_record.rate_limit_rpm
        elif auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            claims = verify_jwt(token)
            request.state.organization_id = claims["organization_id"]
            request.state.api_key_id = None
            request.state.rate_limit_rpm = 60
        else:
            raise AuthenticationError("Missing authentication: provide X-API-Key or Authorization Bearer header")

        org = await resolve_organization(request.state.organization_id, pool)
        request.state.organization = org

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # {key_id: [(timestamp, ...)]}
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only rate-limit after auth has run
        api_key_id = getattr(request.state, "api_key_id", None)
        if api_key_id is None:
            return await call_next(request)

        rpm = getattr(request.state, "rate_limit_rpm", 60)
        now = time.time()
        window_start = now - 60

        # Clean old entries
        entries = self._requests[api_key_id]
        self._requests[api_key_id] = [t for t in entries if t > window_start]

        if len(self._requests[api_key_id]) >= rpm:
            raise RateLimitExceededError(
                f"Rate limit of {rpm} requests per minute exceeded"
            )

        self._requests[api_key_id].append(now)
        return await call_next(request)
