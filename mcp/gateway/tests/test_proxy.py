"""proxy.py：懒 spawn、透传、崩溃重启、空闲回收、冷却、并发串行。"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from conftest import make_manager

from proxy import BackendUnavailable, UnknownTool


async def test_lazy_then_call(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    session = manager.sessions["fake"]
    assert not session.running
    assert session.spawn_count == 0

    result = await manager.call("echo", {"text": "hi"})
    assert result.content[0].text == "hi"  # type: ignore[union-attr]
    assert result.isError is not True
    assert result.structuredContent == {"result": "hi"}
    assert session.spawn_count == 1
    assert session.running


async def test_unknown_tool(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    with pytest.raises(UnknownTool, match="nope"):
        await manager.call("nope", {})


async def test_error_result_passthrough(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    result = await manager.call("fail", {})
    assert result.isError is True
    assert "故意失败" in result.content[0].text  # type: ignore[union-attr]


async def test_crash_then_restart(tmp_path: Path) -> None:
    # cooldown_base=0：崩溃后立即可重启，验证重启路径本身
    manager = make_manager(tmp_path, cooldown_base=0)
    with pytest.raises(BackendUnavailable, match="连接中断"):
        await manager.call("boom", {})
    session = manager.sessions["fake"]
    assert not session.running

    result = await manager.call("echo", {"text": "again"})
    assert result.content[0].text == "again"  # type: ignore[union-attr]
    assert session.spawn_count == 2


async def test_cooldown_after_repeated_crash(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    session = manager.sessions["fake"]
    with pytest.raises(BackendUnavailable, match="连接中断"):
        await manager.call("boom", {})
    # 第一次早夭已进入冷却：后续调用直接被冷却挡下，不再反复拉起
    for _ in range(2):
        with pytest.raises(BackendUnavailable, match="冷却"):
            await manager.call("boom", {})
    assert session.cooldown_remaining > 0
    with pytest.raises(BackendUnavailable, match="冷却"):
        await manager.call("echo", {"text": "x"})


async def test_idle_reap_and_respawn(tmp_path: Path) -> None:
    manager = make_manager(tmp_path, idle_timeout=0.3)
    session = manager.sessions["fake"]
    await manager.call("echo", {"text": "first"})
    pid = session.last_pid
    assert pid is not None

    await asyncio.sleep(0.6)
    assert await session.reap_if_idle() is True
    assert not session.running

    # 进程树确实死亡（trampoline 与 base 解释器都被回收）
    probe = await asyncio.create_subprocess_exec(
        "tasklist",
        "/FI",
        f"PID eq {pid}",
        "/NH",
        stdout=asyncio.subprocess.PIPE,
    )
    out = (await probe.stdout.read()).decode(errors="replace") if probe.stdout else ""
    assert str(pid) not in out

    # 冷启动后可继续服务
    result = await manager.call("echo", {"text": "second"})
    assert result.content[0].text == "second"  # type: ignore[union-attr]


async def test_reap_skipped_when_active(tmp_path: Path) -> None:
    manager = make_manager(tmp_path, idle_timeout=0.2)
    session = manager.sessions["fake"]

    # holder 必须活跃到检查循环结束（固定次数调用约 0.9s 就会跑完，
    # 而检查循环 1.2s，后半段会话合法空闲导致 reap=True 的假失败）
    done = asyncio.Event()

    async def hold_call() -> None:
        i = 0
        while not done.is_set():
            await manager.call("add", {"a": i, "b": 1})
            i += 1
            await asyncio.sleep(0.05)

    holder = asyncio.create_task(hold_call())
    try:
        for _ in range(6):
            await asyncio.sleep(0.2)
            assert await session.reap_if_idle() is False
    finally:
        done.set()
        await holder
    assert session.running


async def test_concurrent_calls_serialize(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    results = await asyncio.gather(
        *(manager.call("echo", {"text": f"n{i}"}) for i in range(4))
    )
    got = {r.content[0].text for r in results}  # type: ignore[union-attr]
    assert got == {f"n{i}" for i in range(4)}
    assert manager.sessions["fake"].spawn_count == 1


async def test_shutdown_prevents_respawn(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    await manager.call("echo", {"text": "x"})
    await manager.shutdown()
    with pytest.raises(BackendUnavailable, match="已随网关关闭"):
        await manager.call("echo", {"text": "y"})


async def test_spawn_failure_cooldown(tmp_path: Path) -> None:
    from conftest import make_fake_spec, make_manifest

    bad = make_fake_spec(tmp_path)
    bad = type(bad)(
        key=bad.key,
        server_dir=bad.server_dir,
        venv_argv=("definitely-missing-exe-xyz", "arg"),
        uv_argv=bad.uv_argv,
    )
    from proxy import GatewayManager

    manager = GatewayManager(
        make_manifest(),  # type: ignore[arg-type]
        specs={"fake": bad},  # type: ignore[arg-type]
    )
    with pytest.raises(BackendUnavailable, match="启动失败"):
        await manager.call("echo", {"text": "x"})
    with pytest.raises(BackendUnavailable, match="冷却"):
        await manager.call("echo", {"text": "x"})
