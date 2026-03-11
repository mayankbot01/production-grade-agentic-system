"""Custom middleware for tracking metrics and other cross-cutting concerns."""

import time
from typing import Callable

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config.settings import settings
from src.system.logs import bind_context, clear_context
from src.system.telemetry import (
    db_connections,
    http_request_duration_seconds,
    http_requests_total,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking HTTP request metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track metrics for each request."""
        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(method=request.method, endpoint=request.url.path, status=status_code).inc()
            http_request_duration_seconds.labels(method=request.method, endpoint=request.url.path).observe(duration)
        return response


class LoggingContextMiddleware(BaseHTTPMiddleware):
    """Middleware for adding user_id and session_id to logging context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Extract user_id and session_id from authenticated requests and add to logging context."""
        try:
            clear_context()
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                    session_id = payload.get("sub")
                    if session_id:
                        bind_context(session_id=session_id)
                except JWTError:
                    pass
            response = await call_next(request)
            if hasattr(request.state, "user_id"):
                bind_context(user_id=request.state.user_id)
            return response
        finally:
            clear_context()
