"""生成网关静态工具清单 tools.json。

用法（在 mcp/gateway 下）：
    uv run scripts/dump_manifest.py [--only fetch,ocr,...]

逐后端以 uv run 方式启动（与各客户端配置一致），完成 MCP 握手后拉取
tools/list，落盘每个工具的 name / backend / description / inputSchema /
outputSchema / annotations。habitica 由本脚本从仓库根 .env 注入
HABITICA_* 环境变量（其余后端凭据走各自 dotenv 向上查找，无需处理）。

任一后端失败时仍会写入成功的部分，但退出码为 1，便于 CI 与人工发现缺失。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402
from mcp.types import Tool  # noqa: E402

from backends import BACKENDS, BackendSpec, env_for  # noqa: E402

TOOLS_JSON = Path(__file__).resolve().parents[1] / "tools.json"


def _tool_entry(backend: str, tool: Tool) -> dict[str, object]:
    entry: dict[str, object] = {
        "name": tool.name,
        "backend": backend,
        "description": tool.description or "",
        "inputSchema": tool.inputSchema,
    }
    if tool.outputSchema:
        entry["outputSchema"] = tool.outputSchema
    if tool.annotations:
        entry["annotations"] = tool.annotations.model_dump(exclude_none=True)
    return entry


async def dump_one(spec: BackendSpec) -> list[dict[str, object]]:
    argv = spec.uv_argv
    params = StdioServerParameters(
        command=argv[0],
        args=list(argv[1:]),
        cwd=str(spec.server_dir),
        env={**os.environ, **env_for(spec)},
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
    return [_tool_entry(spec.key, tool) for tool in result.tools]


async def run(selected: list[str]) -> int:
    collected: list[dict[str, object]] = []
    failed: list[tuple[str, str]] = []
    for key in selected:
        spec = BACKENDS[key]
        try:
            tools = await dump_one(spec)
        except Exception as exc:  # noqa: BLE001 — 汇总所有失败后统一报告
            failed.append((key, f"{type(exc).__name__}: {exc}"))
            print(f"[dump] {key:<8} FAILED  {exc}", file=sys.stderr)
            continue
        collected.extend(tools)
        print(f"[dump] {key:<8} {len(tools)} tools")

    names = [str(t["name"]) for t in collected]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        print(f"[dump] 工具名跨后端冲突：{sorted(duplicates)}", file=sys.stderr)
        return 2

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "backends": sorted(selected),
        "tools": sorted(collected, key=lambda t: str(t["name"])),
    }
    TOOLS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[dump] 写入 {TOOLS_JSON}（{len(collected)} tools）")
    if failed:
        print(
            "[dump] 有后端失败，清单不完整；habitica 失败通常缺 HABITICA_* 凭据"
            "（补录仓库根 .env 后重跑）",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        default=",".join(BACKENDS),
        help=f"逗号分隔的后端子集，默认全部：{','.join(BACKENDS)}",
    )
    keys = [k.strip() for k in parser.parse_args().only.split(",") if k.strip()]
    unknown = [k for k in keys if k not in BACKENDS]
    if unknown:
        parser.error(f"未知后端：{unknown}（可选：{','.join(BACKENDS)}）")
    raise SystemExit(asyncio.run(run(keys)))


if __name__ == "__main__":
    main()
