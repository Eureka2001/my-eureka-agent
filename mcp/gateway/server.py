"""eureka MCP 网关：把本地 MCP server 聚合为单入口。

- tools/list 由静态清单 tools.json 应答（零后端 spawn）；
- tools/call 按需拉起对应后端子进程并以 MCP client 代理，结果原样透传；
- 后端空闲回收 / 崩溃退避重启由 proxy.GatewayManager 负责。

transport 双模（对齐 fetch 等既有 server 的惯例）：默认 stdio；
`--http` 或 MCP_TRANSPORT=http 走 streamable-http（默认 127.0.0.1:1820）。
stdio 铁律：诊断只写 stderr。
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from backends import GATEWAY_DIR
from manifest import Manifest, load_manifest
from proxy import BackendUnavailable, GatewayManager, UnknownTool

DEFAULT_PORT = 1820

logger = logging.getLogger("eureka.gateway")


def build_server(manifest: Manifest, manager: GatewayManager) -> Server:
    """组装低层 Server：清单应答 + 调用分发，CallToolResult 原样透传。"""

    server = Server("eureka")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return manifest.mcp_tools()

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any]
    ) -> types.CallToolResult:
        try:
            return await manager.call(name, arguments)
        except (UnknownTool, BackendUnavailable) as exc:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=str(exc))],
                isError=True,
            )

    return server


def _transport() -> str:
    if "--http" in sys.argv:
        return "streamable-http"
    return os.environ.get("MCP_TRANSPORT", "stdio").lower()


def _setup_logging(transport: str) -> None:
    handlers: list[logging.Handler] = []
    # pythonw 无控制台时 sys.stderr 为 None，跳过控制台 handler
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler(sys.stderr))
    file_env = os.environ.get("GATEWAY_LOG_FILE", "")
    use_file = bool(file_env) or (
        transport in ("http", "streamable-http") and file_env != "0"
    )
    if use_file:
        path = (
            Path(file_env)
            if file_env not in ("", "0")
            else (GATEWAY_DIR / "logs" / "gateway.log")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                path, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
            )
        )
    if not handlers:
        handlers.append(logging.NullHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )
    # SDK 逐请求的 INFO 噪音（stateless 会话终止、请求分派）静音，保留错误
    for noisy in ("mcp.server.streamable_http", "mcp.server.lowlevel.server"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _port_busy(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _quiet_sigint() -> None:
    """HTTP 模式下吞掉信号重抛，避免 Ctrl+C 退出时打印 KeyboardInterrupt 堆栈。

    uvicorn 优雅关停后会把捕获的信号重抛给「原始 handler」；默认情况下 SIGINT
    落到 asyncio.Runner 的中断处理器（注入 KeyboardInterrupt），SIGBREAK 则是
    默认硬终止（finally 都来不及跑）。装上这个不 raise 的 handler 后：Runner
    检测到非默认 handler 不会再接管，uvicorn 恢复并重抛到的也是它——serve()
    正常返回，退出路径的清理得以执行。
    """

    def _handler(signum: int, frame: Any) -> None:  # noqa: ARG001
        pass

    signal.signal(signal.SIGINT, _handler)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, _handler)


async def _run_stdio(server: Server, manager: GatewayManager) -> None:
    options = server.create_initialization_options()
    reap_task = asyncio.create_task(manager.reap_loop())
    try:
        async with stdio_server() as (reader, writer):
            await server.run(reader, writer, options)
    finally:
        reap_task.cancel()
        with suppress(asyncio.CancelledError):
            await reap_task
        await manager.shutdown()
        logger.info("gateway (stdio) shut down, backends released")


async def _run_http(server: Server, manager: GatewayManager) -> None:
    import uvicorn
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.routing import Mount

    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", str(DEFAULT_PORT)))
    if _port_busy(host, port):
        logger.warning("%s:%s 已有实例在监听，本进程退出（单实例保护）", host, port)
        return

    session_manager = StreamableHTTPSessionManager(
        app=server, stateless=True, json_response=True
    )

    async def handle(scope: Any, receive: Any, send: Any) -> None:
        await session_manager.handle_request(scope, receive, send)

    @asynccontextmanager
    async def lifespan(_: Any) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    app = Starlette(routes=[Mount("/", app=handle)], lifespan=lifespan)
    # log_config=None：跳过 uvicorn 自带 dictConfig——其 formatter 会探测
    # sys.stdout.isatty()，pythonw（无控制台）下 sys.stdout 为 None 直接崩溃；
    # 日志统一走本文件 _setup_logging 的 root 配置
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_config=None,
        log_level="warning",
        access_log=False,
    )
    uvicorn_server = uvicorn.Server(config)

    reap_task = asyncio.create_task(manager.reap_loop())
    try:
        await uvicorn_server.serve()
    finally:
        reap_task.cancel()
        with suppress(asyncio.CancelledError):
            await reap_task
        await manager.shutdown()
        logger.info("gateway (http) shut down, backends released")


def main() -> None:
    transport = _transport()
    if transport not in ("stdio", "http", "streamable-http"):
        print(f"不支持的 transport：{transport}", file=sys.stderr)
        raise SystemExit(2)
    _setup_logging(transport)

    try:
        manifest = load_manifest()
        manager = GatewayManager(
            manifest,
            launcher=os.environ.get("GATEWAY_LAUNCHER", "venv").lower(),
        )
        server = build_server(manifest, manager)
        endpoint = (
            "stdio"
            if transport == "stdio"
            else f"http://{os.environ.get('MCP_HOST', '127.0.0.1')}:{os.environ.get('MCP_PORT', DEFAULT_PORT)}/mcp"
        )
        logger.info(
            "eureka gateway starting: transport=%s, endpoint=%s, tools=%d, backends=%s",
            transport,
            endpoint,
            len(manifest.tools),
            sorted(manifest.backends()),
        )

        if transport == "stdio":
            try:
                asyncio.run(_run_stdio(server, manager))
            except KeyboardInterrupt:
                logger.info("gateway stopped by interrupt")
        else:
            _quiet_sigint()
            try:
                asyncio.run(_run_http(server, manager))
            except KeyboardInterrupt:
                logger.info("gateway stopped by interrupt")
    except SystemExit:
        raise
    except BaseException:
        # pythonw 无控制台，未捕获异常必须落日志文件，否则静默死亡无法排查
        logger.exception("gateway crashed")
        raise


if __name__ == "__main__":
    main()
