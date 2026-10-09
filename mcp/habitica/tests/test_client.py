import asyncio
import time
from dataclasses import replace

import httpx
import pytest

from client import HabiticaClient, HabiticaError, _retry_after


async def test_authentication_redaction_and_pool_cleanup(settings):
    def handler(request):
        assert request.url == "https://habitica.com/api/v3/user"
        assert request.headers["x-api-user"] == settings.user_id
        assert request.headers["x-api-key"] == settings.api_token
        assert request.headers["x-client"] == settings.client_id
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "name": "reader",
                    "apiToken": settings.api_token,
                    "nested": [
                        {"auth": {"secret": "private"}, "notes": settings.api_token}
                    ],
                },
            },
        )

    async with HabiticaClient(settings, transport=httpx.MockTransport(handler)) as api:
        data = await api.request("GET", "user")
        assert data == {"name": "reader", "nested": [{"notes": "[REDACTED]"}]}
    assert api._http.is_closed


@pytest.mark.parametrize(
    ("status", "payload", "message"),
    [
        (401, {"success": False, "message": "invalid credential"}, "认证"),
        (403, {"success": False}, "权限"),
        (404, {"success": False, "message": "Task not found"}, "Task not found"),
        (200, {"success": False, "message": "Rejected"}, "Rejected"),
        (200, {"success": True}, "缺少 data"),
        (200, [], "失败响应"),
        (500, {"success": False, "message": "Unavailable"}, "可能已生效"),
    ],
)
async def test_api_errors_are_mcp_safe(settings, status, payload, message):
    transport = httpx.MockTransport(lambda _: httpx.Response(status, json=payload))
    async with HabiticaClient(settings, transport=transport) as api:
        with pytest.raises(HabiticaError, match=message):
            await api.request(
                "POST", "tasks/user", body={"text": "task", "type": "todo"}
            )


async def test_rate_limit_sets_cooldown_without_retry(settings):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "120"})

    async with HabiticaClient(settings, transport=httpx.MockTransport(handler)) as api:
        with pytest.raises(HabiticaError, match="120"):
            await api.request("GET", "tasks/user")
        with pytest.raises(HabiticaError, match="冷却"):
            await api.request("GET", "tasks/user")
    assert len(calls) == 1


async def test_exhausted_rate_budget_blocks_next_call(settings):
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={"success": True, "data": []},
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(time.time() + 120),
            },
        )
    )
    async with HabiticaClient(settings, transport=transport) as api:
        assert await api.request("GET", "tags") == []
        with pytest.raises(HabiticaError, match="冷却"):
            await api.request("GET", "tags")


async def test_write_timeout_has_no_retry_and_does_not_echo_credentials(settings):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout(f"hidden {settings.api_token}", request=request)

    async with HabiticaClient(settings, transport=httpx.MockTransport(handler)) as api:
        with pytest.raises(HabiticaError, match="可能已生效") as exc:
            await api.request("POST", "tasks/test-task/score/up")
    assert len(calls) == 1
    assert settings.api_token not in str(exc.value)


async def test_non_json_and_redirects_are_not_followed(settings):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            302, headers={"Location": "https://another-host.example"}, text="redirect"
        )

    async with HabiticaClient(settings, transport=httpx.MockTransport(handler)) as api:
        with pytest.raises(HabiticaError, match="非 JSON"):
            await api.request("GET", "user")
    assert len(calls) == 1


async def test_error_message_redacts_server_echo_of_credential(settings):
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            400, json={"success": False, "message": f"echo {settings.api_token}"}
        )
    )
    async with HabiticaClient(settings, transport=transport) as api:
        with pytest.raises(HabiticaError) as exc:
            await api.request("GET", "user")
    assert settings.api_token not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


async def test_concurrent_calls_are_paced_and_serialized(settings, monkeypatch):
    import client

    timestamp = [100.0]
    delays = []
    start_times = []
    real_sleep = asyncio.sleep

    async def sleep(seconds):
        delays.append(seconds)
        timestamp[0] += seconds
        await real_sleep(0)

    def handler(_):
        start_times.append(timestamp[0])
        return httpx.Response(200, json={"success": True, "data": []})

    monkeypatch.setattr(client.time, "monotonic", lambda: timestamp[0])
    monkeypatch.setattr(client.asyncio, "sleep", sleep)
    settings = replace(settings, interval_seconds=30)
    async with HabiticaClient(settings, transport=httpx.MockTransport(handler)) as api:
        await asyncio.gather(api.request("GET", "tags"), api.request("GET", "tags"))
    assert start_times == [100.0, 130.0]
    assert delays == [30.0]


@pytest.mark.parametrize("value", [None, "nonsense", "nan", "-1", "0"])
def test_invalid_retry_after_uses_safe_default(value):
    assert _retry_after(value) == 30
