"""manifest.py：加载、校验、重复名与未知后端。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manifest import Manifest, ManifestError, ManifestTool, load_manifest


def _write(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "tools.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_manifest_happy_path(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {
            "tools": [
                {
                    "name": "t1",
                    "backend": "fetch",
                    "description": "d",
                    "inputSchema": {"type": "object"},
                    "annotations": {"readOnlyHint": True},
                },
                {
                    "name": "t2",
                    "backend": "search",
                    "description": "",
                    "inputSchema": {"type": "object"},
                },
            ]
        },
    )
    manifest = load_manifest(path)
    assert set(manifest.by_name) == {"t1", "t2"}
    assert manifest.backends() == {"fetch", "search"}
    tools = manifest.mcp_tools()
    assert tools[0].name == "t1"
    assert tools[0].annotations is not None and tools[0].annotations.readOnlyHint


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="dump_manifest"):
        load_manifest(tmp_path / "nope.json")


def test_empty_tools_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, {"tools": []})
    with pytest.raises(ManifestError, match="不含任何工具"):
        load_manifest(path)


def test_unknown_backend_rejected(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        {"tools": [{"name": "t", "backend": "ghost", "inputSchema": {}}]},
    )
    with pytest.raises(ManifestError, match="未知后端 ghost"):
        load_manifest(path)


def test_duplicate_name_rejected() -> None:
    tool = ManifestTool(name="dup", backend="fetch", description="", input_schema={})
    with pytest.raises(ManifestError, match="重复"):
        Manifest([tool, tool])
