"""HTTP 模式冒烟客户端：连接网关 → tools/list → 可选调用一个轻量工具。

用法（在 mcp/gateway 下，先启动网关）：
    uv run server.py --http
    uv run scripts/smoke_http.py [--url http://127.0.0.1:1820/mcp] [--call qr_backends]
"""

from __future__ import annotations

import argparse
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main(url: str, call: str | None) -> None:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = sorted(t.name for t in listed.tools)
            print(f"[smoke] tools/list -> {len(names)} tools: {names}")
            if call:
                result = await session.call_tool(call, {})
                text = result.content[0].text if result.content else "(no content)"
                print(f"[smoke] call {call} -> isError={result.isError}")
                print(f"[smoke] content: {str(text)[:300]}")


def entrypoint() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:1820/mcp")
    parser.add_argument("--call", default=None, help="可选：调用一个无参轻量工具")
    args = parser.parse_args()
    asyncio.run(main(args.url, args.call))


if __name__ == "__main__":
    entrypoint()
