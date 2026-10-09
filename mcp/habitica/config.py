"""Validated environment configuration; credentials are never included in repr."""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlsplit
from uuid import UUID

DEFAULT_API_URL = "https://habitica.com/api/v3"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_INTERVAL_SECONDS = 30.0


@dataclass(frozen=True)
class Settings:
    user_id: str
    api_token: str = field(repr=False)
    client_id: str
    api_url: str = DEFAULT_API_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Load settings without reading any credential file implicitly."""
        values = os.environ if env is None else env
        user_id = _required(values, "HABITICA_USER_ID")
        _validate_uuid(user_id, "HABITICA_USER_ID")
        api_token = _required(values, "HABITICA_API_TOKEN")
        _validate_header(api_token, "HABITICA_API_TOKEN")
        client_id = values.get("HABITICA_CLIENT_ID", "").strip() or (
            f"{user_id}-eureka-habitica"
        )
        _validate_header(client_id, "HABITICA_CLIENT_ID")
        if len(client_id) <= 37 or client_id[36] != "-":
            raise ValueError("HABITICA_CLIENT_ID 必须为 工具作者的UserID-应用名称。")
        _validate_uuid(client_id[:36], "HABITICA_CLIENT_ID 的作者 UserID")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", client_id[37:]):
            raise ValueError("HABITICA_CLIENT_ID 的应用名称只支持英文、数字、._-。")

        api_url = values.get("HABITICA_API_URL", DEFAULT_API_URL).rstrip("/")
        parts = urlsplit(api_url)
        is_loopback = parts.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.query
            or parts.fragment
            or parts.path != "/api/v3"
            or not (parts.scheme == "https" or parts.scheme == "http" and is_loopback)
        ):
            raise ValueError(
                "HABITICA_API_URL 必须是 HTTPS 的 /api/v3 地址；仅本机开发允许 HTTP。"
            )
        try:
            _ = parts.port
        except ValueError:
            raise ValueError("HABITICA_API_URL 端口无效。") from None

        return cls(
            user_id=user_id,
            api_token=api_token,
            client_id=client_id,
            api_url=api_url,
            timeout_seconds=_number(
                values, "HABITICA_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS, minimum=1
            ),
            interval_seconds=_number(
                values,
                "HABITICA_REQUEST_INTERVAL_SECONDS",
                DEFAULT_INTERVAL_SECONDS,
                minimum=DEFAULT_INTERVAL_SECONDS,
            ),
        )


def _required(values: Mapping[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    if not value:
        raise ValueError(f"缺少 {name}，请通过环境变量或 uv --env-file 设置。")
    return value


def _validate_uuid(value: str, name: str) -> None:
    try:
        UUID(value)
    except ValueError:
        raise ValueError(f"{name} 必须是有效 UUID。") from None


def _validate_header(value: str, name: str) -> None:
    if not value.isascii() or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{name} 包含无效的 HTTP header 字符。")


def _number(
    values: Mapping[str, str], name: str, default: float, *, minimum: float
) -> float:
    try:
        number = float(values.get(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} 必须是数值。") from None
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{name} 必须是大于等于 {minimum:g} 的有限数值。")
    return number
