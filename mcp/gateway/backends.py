"""后端注册表：6 个本地 MCP server 的启动描述与凭据注入规则。

被 scripts/dump_manifest.py（转储清单）与 proxy.py（运行期懒 spawn）共用。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

GATEWAY_DIR = Path(__file__).resolve().parent
MCP_ROOT = GATEWAY_DIR.parent
REPO_ROOT = MCP_ROOT.parent


@dataclass(frozen=True)
class BackendSpec:
    """一个后端 server 的两种启动方式与凭据注入前缀。"""

    key: str
    server_dir: Path
    # 运行期直连启动：跳过 uv 层，省 ~25MB 与 1-2s 冷启动
    venv_argv: tuple[str, ...]
    # 转储/开发用：与各客户端配置里的 uv run 形式一致
    uv_argv: tuple[str, ...]
    # 需要从仓库根 .env 注入子进程的变量前缀（后端自身会 dotenv 向上查找的不需要）
    env_prefixes: tuple[str, ...] = ()


def _std(key: str, env_prefixes: tuple[str, ...] = ()) -> BackendSpec:
    server_dir = MCP_ROOT / key
    return BackendSpec(
        key=key,
        server_dir=server_dir,
        venv_argv=(str(server_dir / ".venv" / "Scripts" / "python.exe"), "server.py"),
        uv_argv=(
            "uv",
            "run",
            "--directory",
            str(server_dir),
            "server.py",
        ),
        env_prefixes=env_prefixes,
    )


_SEARCH_DIR = MCP_ROOT / "mcp_server_askecho_search_infinity"

BACKENDS: dict[str, BackendSpec] = {
    "fetch": _std("fetch"),
    "ocr": _std("ocr"),
    "qrcode": _std("qrcode"),
    "vision": _std("vision"),
    "habitica": _std("habitica", env_prefixes=("HABITICA_",)),
    "search": BackendSpec(
        key="search",
        server_dir=_SEARCH_DIR,
        # src-layout 包，入口是 console script 而非 server.py
        venv_argv=(
            str(
                _SEARCH_DIR
                / ".venv"
                / "Scripts"
                / "mcp-server-askecho-search-infinity.exe"
            ),
        ),
        uv_argv=(
            "uv",
            "run",
            "--directory",
            str(_SEARCH_DIR),
            "mcp-server-askecho-search-infinity",
        ),
    ),
}


def parse_env_file(path: Path) -> dict[str, str]:
    """极简 .env 解析：KEY=VALUE，忽略空行与 # 注释，剥配对引号。"""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def env_for(spec: BackendSpec, env_file: Path | None = None) -> dict[str, str]:
    """按前缀从仓库根 .env 提取需注入的变量；已存在于当前环境的不覆盖。"""
    if not spec.env_prefixes:
        return {}
    source = REPO_ROOT / ".env" if env_file is None else env_file
    injected = {
        key: value
        for key, value in parse_env_file(source).items()
        if key.startswith(spec.env_prefixes) and key not in os.environ
    }
    return injected
