"""后端进程生命周期：懒 spawn、per-backend 串行调用、空闲回收、崩溃退避重启。

两个硬约束决定了本文件的形态：
1. Python 进程内模块不可卸载，「释放内存」只能以子进程为单位——
   回收 = 优雅关 stdin（EOF）→ 等待退出 → taskkill /T /F 杀整棵进程树
   （Windows 下 venv python / entry exe 都是 trampoline，会再派生 base
   解释器，只杀直接子进程会留孤儿）。
2. anyio 的 cancel scope 只能由进入它的 task 退出——因此每个后端由一个
   常驻 supervisor 任务独占进程、转发任务与 ClientSession 的生命周期，
   调用/回收方只通过事件与任务句柄发信号。
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from collections.abc import Mapping
from typing import Any

import anyio
import mcp.types as types
from anyio import BrokenResourceError, ClosedResourceError
from anyio.abc import Process
from anyio.streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
)
from anyio.streams.text import TextReceiveStream
from mcp import ClientSession
from mcp.shared.exceptions import McpError
from mcp.shared.message import SessionMessage
from mcp.types import CONNECTION_CLOSED

from backends import BACKENDS, BackendSpec, env_for
from manifest import Manifest, ManifestError

logger = logging.getLogger("eureka.gateway")

DEFAULT_IDLE_TIMEOUT = float(os.environ.get("GATEWAY_IDLE_TIMEOUT", "180"))
DEFAULT_CALL_TIMEOUT = float(os.environ.get("GATEWAY_CALL_TIMEOUT", "600"))
DEFAULT_SPAWN_TIMEOUT = float(os.environ.get("GATEWAY_SPAWN_TIMEOUT", "30"))
DEFAULT_COOLDOWN_BASE = float(os.environ.get("GATEWAY_COOLDOWN_BASE", "5"))
REAP_INTERVAL = float(os.environ.get("GATEWAY_REAP_INTERVAL", "15"))

_GRACE_EXIT_SECONDS = 5.0
_EARLY_DEATH_WINDOW = 10.0
_MAX_COOLDOWN = 60.0

# pythonw 网关自身无控制台：spawn 控制台子进程若不带 CREATE_NO_WINDOW，
# Windows 会为子进程新建可见终端窗口（默认终端应用为 Windows Terminal 时
# 会真的弹出一个终端窗口，GUI 父进程 + 控制台子进程的默认行为）
_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class UnknownTool(Exception):
    """网关清单里不存在该工具。"""


class BackendUnavailable(Exception):
    """后端当前无法服务（冷却中、启动失败、连接中断、调用超时）。"""


def _kill_tree(pid: int) -> None:
    """杀整棵进程树；进程已不存在时静默成功。"""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
            creationflags=_CREATION_FLAGS,
        )
        return
    try:  # pragma: no cover - 本网关只在 Windows 部署
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class BackendSession:
    """单个后端的懒启动会话。

    状态变更（start / retire）与工具调用全部串行在自身锁内；进程与
    ClientSession 的所有权归 _supervisor 任务。
    """

    def __init__(
        self,
        spec: BackendSpec,
        *,
        idle_timeout: float | None = None,
        call_timeout: float | None = None,
        spawn_timeout: float | None = None,
        cooldown_base: float | None = None,
        launcher: str = "venv",
    ) -> None:
        self._spec = spec
        self._idle_timeout = (
            DEFAULT_IDLE_TIMEOUT if idle_timeout is None else idle_timeout
        )
        self._call_timeout = (
            DEFAULT_CALL_TIMEOUT if call_timeout is None else call_timeout
        )
        self._spawn_timeout = (
            DEFAULT_SPAWN_TIMEOUT if spawn_timeout is None else spawn_timeout
        )
        self._cooldown_base = (
            DEFAULT_COOLDOWN_BASE if cooldown_base is None else cooldown_base
        )
        self._argv = spec.uv_argv if launcher == "uv" else spec.venv_argv
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._ready = asyncio.Event()
        self._death_counted: bool | None = None
        self._session: ClientSession | None = None
        self._process: Process | None = None
        self._closed = False
        self._early_deaths = 0
        self._cooldown_until = 0.0
        self._supervisor_error: BaseException | None = None
        self.last_used = time.monotonic()
        self.spawn_count = 0
        self.last_pid: int | None = None

    # ------------------------------------------------------------------ #
    # 对外状态
    # ------------------------------------------------------------------ #

    @property
    def key(self) -> str:
        return self._spec.key

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def cooldown_remaining(self) -> float:
        return max(0.0, self._cooldown_until - time.monotonic())

    async def call(self, tool: str, arguments: dict[str, Any]) -> types.CallToolResult:
        if self._closed:
            raise BackendUnavailable(f"后端 {self.key} 已随网关关闭")
        if self.cooldown_remaining > 0:
            raise BackendUnavailable(
                f"后端 {self.key} 崩溃冷却中，约 {self.cooldown_remaining:.0f}s 后自动恢复"
            )
        self.last_used = time.monotonic()
        async with self._lock:
            session = self._session
            if not self._is_alive():
                if session is not None or self._task is not None:
                    await self._retire_locked(
                        count_death=True, grace_seconds=_GRACE_EXIT_SECONDS
                    )
                session = await self._start_locked()
            assert session is not None
            try:
                with anyio.fail_after(self._call_timeout):
                    result = await session.call_tool(tool, arguments)
            except TimeoutError as exc:
                await self._retire_locked(count_death=False, grace_seconds=0.1)
                raise BackendUnavailable(
                    f"后端 {self.key} 调用超时（{self._call_timeout:.0f}s），"
                    "已强制回收，下次调用自动重启"
                ) from exc
            except McpError as exc:
                # 后端死亡时 SDK 会以 CONNECTION_CLOSED 终结挂起请求
                if exc.error.code != CONNECTION_CLOSED:
                    raise
                await self._retire_locked(
                    count_death=True, grace_seconds=_GRACE_EXIT_SECONDS
                )
                raise BackendUnavailable(
                    f"后端 {self.key} 连接中断（{exc.error.message}），下次调用自动重启"
                ) from exc
            except (BrokenResourceError, ClosedResourceError) as exc:
                await self._retire_locked(
                    count_death=True, grace_seconds=_GRACE_EXIT_SECONDS
                )
                raise BackendUnavailable(
                    f"后端 {self.key} 连接中断（{type(exc).__name__}），下次调用自动重启"
                ) from exc
        self.last_used = time.monotonic()
        return result

    async def reap_if_idle(self) -> bool:
        """空闲超时则回收，返回是否实际回收；有调用进行中则直接跳过。"""
        if not self._is_alive() or self._closed:
            if self._task is not None and not self._lock.locked():
                async with self._lock:
                    await self._retire_locked(
                        count_death=True, grace_seconds=_GRACE_EXIT_SECONDS
                    )
            return False
        if self._lock.locked():
            return False
        async with self._lock:
            if not self._is_alive():
                return False
            if time.monotonic() - self.last_used < self._idle_timeout:
                return False
            await self._retire_locked(
                count_death=False, grace_seconds=_GRACE_EXIT_SECONDS
            )
            logger.info("backend %s idle %.0fs -> reaped", self.key, self._idle_timeout)
            return True

    async def shutdown(self) -> None:
        """网关退出路径：标记永久关闭并回收（此后不再 respawn）。"""
        self._closed = True
        async with self._lock:
            await self._retire_locked(
                count_death=False, grace_seconds=_GRACE_EXIT_SECONDS
            )

    # ------------------------------------------------------------------ #
    # 启动 / 回收
    # ------------------------------------------------------------------ #

    def _is_alive(self) -> bool:
        return (
            self._task is not None
            and not self._task.done()
            and self._session is not None
            and (self._process is None or self._process.returncode is None)
        )

    async def _start_locked(self) -> ClientSession:
        if self.cooldown_remaining > 0:
            raise BackendUnavailable(
                f"后端 {self.key} 崩溃冷却中，约 {self.cooldown_remaining:.0f}s 后自动恢复"
            )
        self._stop = asyncio.Event()
        self._ready = asyncio.Event()
        self._death_counted = None
        self._session = None
        self._process = None
        task = asyncio.create_task(
            self._supervisor(), name=f"eureka-backend-{self.key}"
        )
        self._task = task
        try:
            await asyncio.wait_for(
                asyncio.shield(self._ready.wait()), timeout=self._spawn_timeout
            )
        except asyncio.TimeoutError:
            await self._retire_locked(count_death=True, grace_seconds=1.0)
            raise BackendUnavailable(
                f"后端 {self.key} 启动超时（{self._spawn_timeout:.0f}s）"
            ) from None
        if self._session is None:
            await asyncio.wait({task})
            reason = self._supervisor_error or "未知原因"
            self._supervisor_error = None
            raise BackendUnavailable(f"后端 {self.key} 启动失败：{reason}")
        return self._session

    async def _retire_locked(self, *, grace_seconds: float, count_death: bool) -> None:
        """停止 supervisor：先请求优雅退出，超时则取消任务；杀树由 supervisor 收尾。

        count_death 由调用方裁决：崩溃/异常死亡为 True（计入冷却），
        空闲回收 / 调用超时 / 网关关停为 False。
        """
        task = self._task
        if task is None:
            return
        self._death_counted = count_death
        self._task = None
        self._stop.set()
        stdin = self._process.stdin if self._process is not None else None
        if grace_seconds > 0 and stdin is not None:
            try:
                await stdin.aclose()
            except Exception:
                pass
        done, pending = await asyncio.wait({task}, timeout=grace_seconds)
        if pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # noqa: BLE001 - supervisor 自身异常只记录
                logger.exception("backend %s supervisor 退出异常", self.key)
        self._session = None
        self._process = None

    async def _supervisor(self) -> None:
        """独占后端进程与 ClientSession 生命周期的常驻任务。"""
        argv = list(self._argv)
        env = {**os.environ, **env_for(self._spec)}
        self._supervisor_error = None
        process: Process | None = None
        started_at = time.monotonic()
        ready_ok = False
        try:
            process = await anyio.open_process(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self._spec.server_dir),
                env=env,
                creationflags=_CREATION_FLAGS,
            )
            self._process = process
            self.last_pid = process.pid
            self.spawn_count += 1
            logger.info(
                "backend %s spawned pid=%s (%s)", self.key, process.pid, argv[0]
            )

            read_writer: MemoryObjectSendStream[SessionMessage | Exception]
            read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
            write_stream: MemoryObjectSendStream[SessionMessage]
            write_reader: MemoryObjectReceiveStream[SessionMessage]
            read_writer, read_stream = anyio.create_memory_object_stream(0)
            write_stream, write_reader = anyio.create_memory_object_stream(0)

            async with anyio.create_task_group() as tg:
                tg.start_soon(self._stdout_reader, process, read_writer)
                tg.start_soon(self._stdin_writer, process, write_reader)
                tg.start_soon(self._stderr_reader, process)
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self._session = session
                    started_at = time.monotonic()
                    ready_ok = True
                    self._ready.set()
                    await self._stop.wait()
        except Exception as exc:
            self._supervisor_error = exc
            if ready_ok:
                # 运行期死亡：异常若不上日志，调用方只会看到挂起 + early death
                logger.exception("backend %s supervisor 异常退出", self.key)
        finally:
            self._session = None
            if not ready_ok:
                self._ready.set()
            if process is not None:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        try:
                            await stream.aclose()
                        except Exception:
                            pass
                with anyio.move_on_after(_GRACE_EXIT_SECONDS):
                    await process.wait()
                _kill_tree(process.pid or -1)
                with anyio.move_on_after(_GRACE_EXIT_SECONDS):
                    await process.wait()
            self._record_death(
                lifetime_seconds=time.monotonic() - started_at,
                graceful=not (
                    True if self._death_counted is None else self._death_counted
                ),
            )
            if self._task is not None and self._task.done() is False:
                logger.info("backend %s supervisor exited", self.key)

    def _record_death(self, *, lifetime_seconds: float, graceful: bool) -> None:
        """优雅回收只重置计数；异常早夭才进入指数退避冷却（上限 60s）。"""
        if graceful:
            self._early_deaths = 0
            return
        if lifetime_seconds >= _EARLY_DEATH_WINDOW:
            self._early_deaths = 0
            return
        self._early_deaths += 1
        cooldown = min(
            self._cooldown_base * 2 ** (self._early_deaths - 1), _MAX_COOLDOWN
        )
        self._cooldown_until = time.monotonic() + cooldown
        logger.warning(
            "backend %s early death #%d, cooldown %.0fs",
            self.key,
            self._early_deaths,
            cooldown,
        )

    # ------------------------------------------------------------------ #
    # 进程 stdio 与内存流之间的转发（等价 mcp.client.stdio 的胶水，
    # 但保留进程句柄并额外把 stderr 接进网关日志）
    # ------------------------------------------------------------------ #

    async def _stdout_reader(
        self,
        process: Process,
        writer: MemoryObjectSendStream[SessionMessage | Exception],
    ) -> None:
        assert process.stdout is not None
        try:
            async with writer:
                buffer = ""
                async for chunk in TextReceiveStream(process.stdout):
                    lines = (buffer + chunk).split("\n")
                    buffer = lines.pop()
                    for line in lines:
                        try:
                            message = types.JSONRPCMessage.model_validate_json(line)
                        except Exception as exc:
                            logger.warning(
                                "backend %s stdout 非 JSON-RPC 行（注入异常给会话）: %r",
                                self.key,
                                line[:200],
                            )
                            await writer.send(exc)
                            continue
                        await writer.send(SessionMessage(message))
        except (ClosedResourceError, BrokenResourceError):
            await anyio.lowlevel.checkpoint()

    async def _stdin_writer(
        self,
        process: Process,
        reader: MemoryObjectReceiveStream[SessionMessage],
    ) -> None:
        assert process.stdin is not None
        try:
            async with reader:
                async for message in reader:
                    payload = message.message.model_dump_json(
                        by_alias=True, exclude_none=True
                    )
                    await process.stdin.send((payload + "\n").encode())
        except (ClosedResourceError, BrokenResourceError):
            await anyio.lowlevel.checkpoint()

    async def _stderr_reader(self, process: Process) -> None:
        assert process.stderr is not None
        backend_log = logging.getLogger(f"eureka.gateway.backend.{self.key}")
        try:
            # errors="replace"：后端在 GBK 环境下写的中文诊断是合法输出，
            # 严格解码会让整个 supervisor 会话崩掉、挂死进行中的调用。
            async for chunk in TextReceiveStream(process.stderr, errors="replace"):
                for line in chunk.splitlines():
                    if line.strip():
                        backend_log.info("%s", line)
        except (ClosedResourceError, BrokenResourceError):
            await anyio.lowlevel.checkpoint()


class GatewayManager:
    """清单驱动的分发器：只为清单中实际出现的后端建会话。"""

    def __init__(
        self,
        manifest: Manifest,
        *,
        idle_timeout: float | None = None,
        call_timeout: float | None = None,
        spawn_timeout: float | None = None,
        cooldown_base: float | None = None,
        launcher: str = "venv",
        specs: Mapping[str, BackendSpec] | None = None,
    ) -> None:
        self._manifest = manifest
        registry = dict(BACKENDS) if specs is None else dict(specs)
        self.sessions: dict[str, BackendSession] = {}
        for backend in sorted(manifest.backends()):
            spec = registry.get(backend)
            if spec is None:
                raise ManifestError(f"清单后端 {backend} 不在启动注册表中")
            self.sessions[backend] = BackendSession(
                spec,
                idle_timeout=idle_timeout,
                call_timeout=call_timeout,
                spawn_timeout=spawn_timeout,
                cooldown_base=cooldown_base,
                launcher=launcher,
            )

    async def call(self, name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        tool = self._manifest.by_name.get(name)
        if tool is None:
            raise UnknownTool(
                f"网关没有工具 {name}（清单共 {len(self._manifest.tools)} 个工具）"
            )
        return await self.sessions[tool.backend].call(tool.name, arguments)

    async def reap_loop(self) -> None:
        while True:
            await asyncio.sleep(REAP_INTERVAL)
            for session in self.sessions.values():
                try:
                    await session.reap_if_idle()
                except Exception:
                    logger.exception("reap %s 失败", session.key)

    async def shutdown(self) -> None:
        for session in self.sessions.values():
            try:
                await session.shutdown()
            except Exception:
                logger.exception("shutdown %s 失败", session.key)
