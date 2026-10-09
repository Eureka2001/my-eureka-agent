import json
import os
import sys
from pathlib import Path

import httpx
import pytest
from conftest import ITEM_ID, TAG_ID, TEST_ENV, USER_ID
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from server import create_server


async def test_tool_discovery_annotations_and_schemas(settings):
    transport = httpx.MockTransport(
        lambda _: pytest.fail("Discovery must not call Habitica")
    )
    async with create_connected_server_and_client_session(
        create_server(settings, transport=transport)
    ) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
    assert len(tools) == 15
    assert tools["get_user"].annotations.readOnlyHint is True
    assert tools["delete_task"].annotations.destructiveHint is True
    assert tools["score_task"].annotations.idempotentHint is False
    assert "ctx" not in tools["create_task"].inputSchema["properties"]
    assert "task" in tools["create_task"].inputSchema["required"]
    assert tools["score_task"].inputSchema["properties"]["direction"]["enum"] == [
        "up",
        "down",
    ]


@pytest.mark.parametrize(
    ("tool", "args", "method", "path", "body", "data"),
    [
        (
            "habitica_health",
            {},
            "GET",
            "/user",
            None,
            {"_id": USER_ID, "profile": {"name": "reader"}},
        ),
        (
            "get_user",
            {},
            "GET",
            "/user",
            None,
            {"_id": USER_ID, "stats": {"lvl": 5}, "apiToken": "private"},
        ),
        (
            "list_tasks",
            {"task_type": "completedTodos"},
            "GET",
            "/tasks/user",
            None,
            [{"id": "task", "type": "todo"}],
        ),
        ("get_task", {"task_id": "task"}, "GET", "/tasks/task", None, {"id": "task"}),
        (
            "create_task",
            {"task": {"type": "todo", "text": "读书", "priority": 0.1}},
            "POST",
            "/tasks/user",
            {"type": "todo", "text": "读书", "priority": 0.1},
            {"id": "new-task"},
        ),
        (
            "update_task",
            {"task_id": "task", "changes": {"notes": "", "tags": []}},
            "PUT",
            "/tasks/task",
            {"notes": "", "tags": []},
            {"id": "task", "notes": ""},
        ),
        ("delete_task", {"task_id": "task"}, "DELETE", "/tasks/task", None, {}),
        (
            "score_task",
            {"task_id": "task", "direction": "up"},
            "POST",
            "/tasks/task/score/up",
            None,
            {"gp": 10, "exp": 5},
        ),
        (
            "add_checklist_item",
            {"task_id": "task", "text": "准备"},
            "POST",
            "/tasks/task/checklist",
            {"text": "准备", "completed": False},
            {"checklist": [{"id": ITEM_ID}]},
        ),
        (
            "update_checklist_item",
            {"task_id": "task", "item_id": ITEM_ID, "text": "准备", "completed": True},
            "PUT",
            f"/tasks/task/checklist/{ITEM_ID}",
            {"text": "准备", "completed": True},
            {"checklist": [{"id": ITEM_ID, "completed": True}]},
        ),
        (
            "delete_checklist_item",
            {"task_id": "task", "item_id": ITEM_ID},
            "DELETE",
            f"/tasks/task/checklist/{ITEM_ID}",
            None,
            {"checklist": []},
        ),
        ("list_tags", {}, "GET", "/tags", None, [{"id": TAG_ID, "name": "工作"}]),
        (
            "create_tag",
            {"name": "工作"},
            "POST",
            "/tags",
            {"name": "工作"},
            {"id": TAG_ID},
        ),
        (
            "update_tag",
            {"tag_id": TAG_ID, "name": "学习"},
            "PUT",
            f"/tags/{TAG_ID}",
            {"name": "学习"},
            {"id": TAG_ID},
        ),
        ("delete_tag", {"tag_id": TAG_ID}, "DELETE", f"/tags/{TAG_ID}", None, {}),
    ],
)
async def test_tools_call_official_routes_over_mcp(
    settings, tool, args, method, path, body, data
):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == method
        assert request.url.path == f"/api/v3{path}"
        assert (json.loads(request.content) if request.content else None) == body
        if tool == "list_tasks":
            assert request.url.params["type"] == "completedTodos"
        if tool in {"get_user", "habitica_health"}:
            assert "auth" not in request.url.params["userFields"]
        return httpx.Response(200, json={"success": True, "data": data})

    transport = httpx.MockTransport(handler)
    async with create_connected_server_and_client_session(
        create_server(settings, transport=transport)
    ) as session:
        result = await session.call_tool(tool, args)
    assert not result.isError, result.content
    assert result.structuredContent is not None
    assert len(calls) == 1
    if tool == "get_user":
        assert "apiToken" not in result.structuredContent


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("score_task", {"task_id": "task", "direction": "sideways"}),
        ("get_task", {"task_id": "../user"}),
        ("get_task", {"task_id": "https://untrusted.example"}),
        ("create_task", {"task": {"type": "todo", "text": "task", "priority": 3}}),
        ("update_task", {"task_id": "task", "changes": {"completed": True}}),
        ("create_tag", {"name": " "}),
        ("delete_tag", {"tag_id": "not-uuid"}),
        ("list_tasks", {"task_type": "daily"}),
    ],
)
async def test_invalid_calls_return_mcp_error_without_request(settings, tool, args):
    transport = httpx.MockTransport(
        lambda _: pytest.fail("Invalid parameters reached API")
    )
    async with create_connected_server_and_client_session(
        create_server(settings, transport=transport)
    ) as session:
        result = await session.call_tool(tool, args)
    assert result.isError


async def test_http_failure_is_reported_as_mcp_error(settings):
    transport = httpx.MockTransport(
        lambda _: httpx.Response(401, json={"success": False})
    )
    async with create_connected_server_and_client_session(
        create_server(settings, transport=transport)
    ) as session:
        result = await session.call_tool("get_user")
    assert result.isError
    assert "认证" in result.content[0].text
    assert settings.api_token not in str(result)


async def test_real_stdio_handshake_and_tool_discovery():
    project_dir = Path(__file__).resolve().parents[1]
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("HABITICA_", "MCP_", "FASTMCP_"))
    }
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(project_dir / "server.py")],
        cwd=str(project_dir),
        env={**env, **TEST_ENV, "MCP_TRANSPORT": "http"},
    )
    # sys.executable is this uv-run project's interpreter, never system Python.
    async with stdio_client(params) as streams, ClientSession(*streams) as session:
        initialized = await session.initialize()
        tools = await session.list_tools()
    assert initialized.serverInfo.name == "eureka_habitica"
    assert len(tools.tools) == 15
