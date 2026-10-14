"""server.py：低层 Server 全链路——在内存流上跑完整 MCP 协议。"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

import anyio
from conftest import make_manager, make_manifest
from mcp import ClientSession
from mcp.shared.message import SessionMessage

from server import build_server


async def test_end_to_end_over_memory_streams(tmp_path: Path) -> None:
    manifest = make_manifest()
    manager = make_manager(tmp_path)
    server = build_server(manifest, manager)

    client_to_server, server_read = anyio.create_memory_object_stream[
        SessionMessage | Exception
    ](0)
    server_write, client_read = anyio.create_memory_object_stream[
        SessionMessage | Exception
    ](0)
    options = server.create_initialization_options()
    server_task = asyncio.create_task(server.run(server_read, server_write, options))

    try:
        async with ClientSession(client_read, client_to_server) as session:
            await session.initialize()

            listed = await session.list_tools()
            assert {t.name for t in listed.tools} >= {"echo", "add", "fail", "boom"}
            # tools/list 零 spawn
            assert manager.sessions["fake"].spawn_count == 0

            ok = await session.call_tool("echo", {"text": "e2e"})
            assert ok.content[0].text == "e2e"  # type: ignore[union-attr]
            assert ok.isError is not True
            assert manager.sessions["fake"].spawn_count == 1

            unknown = await session.call_tool("nope", {})
            assert unknown.isError is True

            failed = await session.call_tool("fail", {})
            assert failed.isError is True
            assert "故意失败" in failed.content[0].text  # type: ignore[union-attr]
    finally:
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task
        await manager.shutdown()
