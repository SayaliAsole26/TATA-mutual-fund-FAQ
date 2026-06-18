"""Simple in-memory rate limiter for /api/chat (Phase 5)."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config.settings import get_settings


class ChatRateLimitMiddleware(BaseHTTPMiddleware):
    """Limit POST /api/chat to N requests per minute per client IP."""

    def __init__(self, app, requests_per_minute: int | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self.requests_per_minute = requests_per_minute or settings.chat_rate_limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_limited(self, ip: str) -> bool:
        if self.requests_per_minute <= 0:
            return False
        now = time.monotonic()
        window = self._hits[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.requests_per_minute:
            return True
        window.append(now)
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "POST" and request.url.path.rstrip("/") == "/api/chat":
            ip = self._client_ip(request)
            if self._is_limited(ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "type": "error",
                        "message": "Too many requests. Please wait a minute and try again.",
                    },
                )
        return await call_next(request)
