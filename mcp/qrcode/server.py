"""QR Code 解码 MCP server。

定位：确定性、离线、零成本的本地解码层（不依赖 VLM，避免幻觉）。
两个后端，自动 fallback：
  1. pyzbar —— 轻量、支持多码与多种条码格式；需系统 libzbar（Windows 需 ZBar.dll）。
  2. OpenCV WeChatQRCode —— 工业级，对模糊/倾斜/反光鲁棒；需 4 个模型文件。

VLM 兜底刻意不放在本 server —— 那是 vision server 的职责；本工具追求确定性。

transport 双模：默认 stdio；设环境变量 MCP_TRANSPORT=http 或加 --http 走 streamable-http。
注意：stdio 模式下所有诊断信息只写 stderr，绝不写 stdout（会污染协议流）。
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path
from typing import Any

import cv2
import httpx
import numpy as np
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("eureka_qrcode")


# --------------------------------------------------------------------------- #
# 后端 1：pyzbar（运行时可能因缺 libzbar 导入失败，需优雅降级）
# --------------------------------------------------------------------------- #
try:
    from pyzbar.pyzbar import decode as _pyzbar_decode

    _HAS_PYZBAR = True
    _PYZBAR_ERR = ""
except Exception as e:  # 缺 libzbar / ZBar.dll 时抛出
    _HAS_PYZBAR = False
    _PYZBAR_ERR = f"{type(e).__name__}: {e}"


# --------------------------------------------------------------------------- #
# 后端 2：OpenCV WeChatQRCode（需 4 个模型文件）
# --------------------------------------------------------------------------- #
_MODELS_DIR = Path(os.environ.get("QR_MODELS_DIR", Path(__file__).parent / "models"))
_WECHAT_MODEL_FILES = ("det.prototxt", "det.caffemodel", "sr.prototxt", "sr.caffemodel")
_wechat_detector: Any = None  # 懒加载，首次用到时初始化


def _load_wechat_detector() -> Any:
    """模型齐全则返回 WeChatQRCode 实例，否则返回 None。"""
    paths = [_MODELS_DIR / f for f in _WECHAT_MODEL_FILES]
    if not all(p.exists() for p in paths):
        return None
    try:
        return cv2.wechat_qrcode_WeChatQRCode(*(str(p) for p in paths))
    except Exception as e:  # pragma: no cover - 模型损坏等极端情况
        print(f"[qrcode] wechat-qrcode 初始化失败: {e}", file=sys.stderr)
        return None


# --------------------------------------------------------------------------- #
# 图像加载：本地路径 | http(s) URL | data: URI | 裸 base64
# --------------------------------------------------------------------------- #
def _load_image(image: str) -> np.ndarray:
    if image.startswith(("http://", "https://")):
        resp = httpx.get(image, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
        raw = resp.content
    elif image.startswith("data:"):
        raw = base64.b64decode(image.split(",", 1)[-1])
    else:
        # 优先按文件路径读，失败再当裸 base64 试
        p = Path(image)
        if p.exists():
            raw = p.read_bytes()
        else:
            try:
                raw = base64.b64decode(image, validate=False)
            except Exception as e:
                raise ValueError(
                    f"无法解析 image 参数（既非存在路径，也非合法 base64/URL）：{e}"
                ) from e

    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("字节流无法解码为图像，请检查 URL/路径/base64 是否有效")
    return img


def _format_unmatched_hint() -> str:
    hints: list[str] = []
    if not _HAS_PYZBAR:
        hints.append(f"pyzbar 不可用（{_PYZBAR_ERR}）")
    if _wechat_detector is None and _load_wechat_detector() is None:
        hints.append(
            f"wechat-qrcode 模型缺失（放入 {_MODELS_DIR}：{', '.join(_WECHAT_MODEL_FILES)}）"
        )
    return "；后端未就绪：" + "；".join(hints) if hints else ""


# --------------------------------------------------------------------------- #
# MCP 工具
# --------------------------------------------------------------------------- #
@mcp.tool()
def decode_qrcode(image: str) -> str:
    """从图片解码 QR 码及条形码，返回每个码的内容，每行一个。

    本工具为确定性、离线解码，不调用 VLM。适合需要 100% 可靠结果、或断网场景。

    Args:
        image: 图片来源，支持以下任一形式：
            - 本地文件绝对/相对路径
            - http(s) URL
            - data: URI（data:image/png;base64,...）
            - 裸 base64 字符串
    """
    img = _load_image(image)
    found: list[dict[str, str]] = []

    # 后端 1：pyzbar
    if _HAS_PYZBAR:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for r in _pyzbar_decode(gray):
            found.append(
                {
                    "data": r.data.decode("utf-8", "replace"),
                    "type": r.type,
                    "backend": "pyzbar",
                }
            )

    # 后端 2：wechat（仅当 pyzbar 无结果时启用，避免重复解码）
    if not found:
        global _wechat_detector
        if _wechat_detector is None:
            _wechat_detector = _load_wechat_detector()
        if _wechat_detector is not None:
            texts, _ = _wechat_detector.detectAndDecode(img)
            for t in texts:
                if t:
                    found.append({"data": t, "type": "QRCode", "backend": "wechat"})

    if not found:
        return f"未检测到二维码。{_format_unmatched_hint()}"

    return "\n".join(item["data"] for item in found)


@mcp.tool()
def qr_backends() -> str:
    """报告当前可用的解码后端及其状态，便于排查环境问题。"""
    global _wechat_detector
    wechat_ok = (_wechat_detector is not None) or (_load_wechat_detector() is not None)
    lines = [
        f"pyzbar: {'就绪' if _HAS_PYZBAR else '不可用 — ' + _PYZBAR_ERR}",
        f"wechat-qrcode: {'就绪' if wechat_ok else f'模型缺失 — 期望目录 {_MODELS_DIR}'}",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 入口：双模 transport
# --------------------------------------------------------------------------- #
def _transport() -> str:
    if "--http" in sys.argv:
        return "streamable-http"
    return os.environ.get("MCP_TRANSPORT", "stdio").lower()


if __name__ == "__main__":
    mode = _transport()
    if mode in ("http", "streamable-http", "sse"):
        mcp.settings.host = os.environ.get("MCP_HOST", "127.0.0.1")
        mcp.settings.port = int(os.environ.get("MCP_PORT", "8000"))
        print(
            f"[qrcode] streamable-http @ {mcp.settings.host}:{mcp.settings.port}",
            file=sys.stderr,
        )
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
