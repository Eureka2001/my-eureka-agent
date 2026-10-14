"""tools.json 静态清单的加载、校验与低层 MCP Tool 转换。

清单是网关对 tools/list 的唯一应答来源——读取它不 spawn 任何后端，
这是「0 功能初始状态轻量」的关键。后端增改工具后重跑
`uv run scripts/dump_manifest.py` 再生成。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import mcp.types as types

from backends import BACKENDS, GATEWAY_DIR


class ManifestError(Exception):
    """清单文件缺失或内容非法。"""


@dataclass(frozen=True)
class ManifestTool:
    name: str
    backend: str
    description: str
    input_schema: dict[str, object]
    output_schema: dict[str, object] | None = None
    annotations: dict[str, object] | None = None

    def to_mcp_tool(self) -> types.Tool:
        return types.Tool(
            name=self.name,
            description=self.description or None,
            inputSchema=self.input_schema,  # type: ignore[arg-type]
            outputSchema=self.output_schema,  # type: ignore[arg-type]
            annotations=(
                types.ToolAnnotations(**self.annotations)  # type: ignore[arg-type]
                if self.annotations
                else None
            ),
        )


class Manifest:
    """已校验的静态工具清单。"""

    def __init__(self, tools: list[ManifestTool]) -> None:
        self.tools = tuple(tools)
        self.by_name: dict[str, ManifestTool] = {}
        for tool in self.tools:
            if tool.name in self.by_name:
                raise ManifestError(f"工具名重复：{tool.name}")
            self.by_name[tool.name] = tool

    def backends(self) -> set[str]:
        return {tool.backend for tool in self.tools}

    def mcp_tools(self) -> list[types.Tool]:
        return [tool.to_mcp_tool() for tool in self.tools]


def load_manifest(path: Path | None = None) -> Manifest:
    path = path or GATEWAY_DIR / "tools.json"
    if not path.is_file():
        raise ManifestError(
            f"缺少 {path}；请先运行 `uv run scripts/dump_manifest.py` 生成清单"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{path} 不是合法 JSON：{exc}") from exc

    tools: list[ManifestTool] = []
    for index, raw in enumerate(data.get("tools", [])):
        if not isinstance(raw, dict):
            raise ManifestError(f"{path} 第 {index} 个工具不是对象")
        try:
            tool = ManifestTool(
                name=str(raw["name"]),
                backend=str(raw["backend"]),
                description=str(raw.get("description") or ""),
                input_schema=dict(raw["inputSchema"]),
                output_schema=(
                    dict(raw["outputSchema"]) if raw.get("outputSchema") else None
                ),
                annotations=dict(raw["annotations"])
                if raw.get("annotations")
                else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestError(f"{path} 第 {index} 个工具内容非法：{exc}") from exc
        if tool.backend not in BACKENDS:
            raise ManifestError(
                f"工具 {tool.name} 指向未知后端 {tool.backend}"
                f"（已知：{sorted(BACKENDS)}）"
            )
        tools.append(tool)
    if not tools:
        raise ManifestError(f"{path} 不含任何工具，拒绝启动空网关")
    return Manifest(tools)
