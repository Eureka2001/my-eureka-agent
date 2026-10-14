"""测试用最小后端：echo / add / fail / boom（boom 直接退进程模拟崩溃）。"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fake_backend")


@mcp.tool()
def echo(text: str) -> str:
    """原样返回 text。"""
    return text


@mcp.tool()
def add(a: int, b: int) -> int:
    """返回 a + b。"""
    return a + b


@mcp.tool()
def fail() -> str:
    """抛异常，后端应返回 isError 结果。"""
    raise ValueError("故意失败")


@mcp.tool()
def boom() -> str:
    """直接退出进程，模拟后端崩溃。"""
    os._exit(1)


if __name__ == "__main__":
    mcp.run(transport="stdio")
