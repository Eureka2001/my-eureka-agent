"""Pooled async Habitica API client with pacing and no automatic mutation retries."""

from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from typing import Any

import httpx

from config import DEFAULT_INTERVAL_SECONDS, Settings

MAX_ERROR_LENGTH = 500
SENSITIVE_KEYS = frozenset(
    {"apitoken", "api_token", "x-api-key", "password", "auth", "authentication"}
)


class HabiticaError(Exception):
    """An actionable API error safe to expose to MCP clients."""


class HabiticaClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._lock = asyncio.Lock()
        self._next_request_at = 0.0
        self._blocked_until = 0.0
        self._http = httpx.AsyncClient(
            base_url=f"{settings.api_url}/",
            headers={
                "x-api-user": settings.user_id,
                "x-api-key": settings.api_token,
                "x-client": settings.client_id,
                "Accept": "application/json",
            },
            timeout=settings.timeout_seconds,
            follow_redirects=False,
            transport=transport,
        )

    async def __aenter__(self) -> HabiticaClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._http.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Make one paced request and unwrap Habitica's success/data envelope."""
        async with self._lock:
            now = time.monotonic()
            if self._blocked_until > now:
                remaining_seconds = math.ceil(self._blocked_until - now)
                raise HabiticaError(
                    f"Habitica 限流冷却中，请 {remaining_seconds} 秒后再调用。"
                )
            delay = self._next_request_at - now
            if delay > 0:
                await asyncio.sleep(delay)
            self._next_request_at = time.monotonic() + self.settings.interval_seconds
            uncertain = (
                "操作可能已生效；请先查询状态，再决定是否重试。"
                if method != "GET"
                else "请稍后重试。"
            )
            try:
                response = await self._http.request(
                    method, path, params=params, json=body
                )
            except httpx.TimeoutException:
                raise HabiticaError(f"Habitica 请求超时。{uncertain}") from None
            except httpx.RequestError:
                raise HabiticaError(f"无法连接 Habitica。{uncertain}") from None

            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                seconds = _retry_after(response.headers.get("Retry-After"))
                self._blocked_until = time.monotonic() + seconds
                raise HabiticaError(
                    f"Habitica 请求过多，请 {math.ceil(seconds)} 秒后重试。"
                )

            if response.headers.get("X-RateLimit-Remaining") == "0":
                try:
                    reset = float(response.headers.get("X-RateLimit-Reset", ""))
                    if math.isfinite(reset):
                        self._blocked_until = time.monotonic() + max(
                            0, reset - time.time()
                        )
                except ValueError:
                    pass

            try:
                payload = response.json()
            except ValueError:
                raise HabiticaError(
                    f"Habitica 返回非 JSON 响应（HTTP {response.status_code}）。{uncertain}"
                ) from None

            if (
                not response.is_success
                or not isinstance(payload, dict)
                or payload.get("success") is not True
            ):
                if response.status_code in {
                    HTTPStatus.UNAUTHORIZED,
                    HTTPStatus.FORBIDDEN,
                }:
                    raise HabiticaError(
                        "Habitica 认证或权限检查失败，请检查 User ID、API Token 和操作权限。"
                    )
                message = "Habitica 返回失败响应。"
                if isinstance(payload, dict) and isinstance(
                    payload.get("message"), str
                ):
                    message = self._redact(payload["message"])[:MAX_ERROR_LENGTH]
                suffix = (
                    uncertain if method != "GET" and response.is_server_error else ""
                )
                raise HabiticaError(
                    f"HTTP {response.status_code}: {message} {suffix}".strip()
                )

            if "data" not in payload:
                raise HabiticaError(f"Habitica 响应缺少 data 字段。{uncertain}")
            return self._sanitize(payload["data"])

    def _redact(self, value: str) -> str:
        return value.replace(self.settings.api_token, "[REDACTED]")

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._sanitize(item)
                for key, item in value.items()
                if key.lower() not in SENSITIVE_KEYS
            }
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return self._redact(value) if isinstance(value, str) else value


def _retry_after(value: str | None) -> float:
    if value is not None:
        try:
            seconds = float(value)
            if math.isfinite(seconds) and seconds >= 0:
                return max(seconds, DEFAULT_INTERVAL_SECONDS)
        except ValueError:
            try:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                return max(
                    (date - datetime.now(timezone.utc)).total_seconds(),
                    DEFAULT_INTERVAL_SECONDS,
                )
            except (TypeError, ValueError, OverflowError):
                pass
    return DEFAULT_INTERVAL_SECONDS
