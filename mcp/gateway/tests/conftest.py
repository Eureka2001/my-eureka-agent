"""测试公共件：假后端 spec / 手工 manifest / manager 工厂。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backends import BackendSpec  # noqa: E402
from manifest import Manifest, ManifestTool  # noqa: E402
from proxy import GatewayManager  # noqa: E402

FAKE_BACKEND = Path(__file__).resolve().parent / "fake_backend.py"

_OBJ = {"type": "object", "properties": {}, "required": []}


def make_fake_spec(tmp_path: Path) -> BackendSpec:
    argv = (sys.executable, str(FAKE_BACKEND))
    return BackendSpec(
        key="fake",
        server_dir=tmp_path,
        venv_argv=argv,
        uv_argv=argv,
    )


def make_manifest() -> Manifest:
    def tool(name: str) -> ManifestTool:
        return ManifestTool(
            name=name,
            backend="fake",
            description=f"fake tool {name}",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"] if name == "echo" else [],
            },
        )

    return Manifest([tool(n) for n in ("echo", "add", "fail", "boom")])


def make_manager(tmp_path: Path, **kwargs: object) -> GatewayManager:
    return GatewayManager(
        make_manifest(),  # type: ignore[arg-type]
        specs={"fake": make_fake_spec(tmp_path)},  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )
