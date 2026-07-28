"""OCR MCP server —— 阿里云通用文字识别。

定位：**更便宜、适合 PDF/文档文字抽取**（PDF 用 OCR 远优于逐页丢给 Vision）。
后端：阿里云 ocr-api 服务的 RecognizeGeneral（支持图片与 PDF，输出 markdown 文本）。

凭据来自环境变量（绝不入库）：
  ALIYUN_OCR_AK_ID      AccessKey ID
  ALIYUN_OCR_AK_SECRET  AccessKey Secret
  ALIYUN_OCR_ENDPOINT   可选，默认 ocr-api.cn-hangzhou.aliyuncs.com

transport 双模：默认 stdio；MCP_TRANSPORT=http 或 --http 走 streamable-http。
stdio 模式诊断信息只写 stderr。
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ocr")


def _creds() -> tuple[str, str, str]:
    ak = os.environ.get("ALIYUN_OCR_AK_ID", "").strip()
    sk = os.environ.get("ALIYUN_OCR_AK_SECRET", "").strip()
    endpoint = os.environ.get("ALIYUN_OCR_ENDPOINT", "ocr-api.cn-hangzhou.aliyuncs.com").strip()
    if not ak or not sk:
        raise RuntimeError(
            "缺少阿里云凭据：请设置环境变量 ALIYUN_OCR_AK_ID 与 ALIYUN_OCR_AK_SECRET。"
        )
    return ak, sk, endpoint


def _client():
    """懒加载阿里云 OCR 客户端（凭据缺失时抛错）。"""
    from alibabacloud_ocr_api20210707.client import Client as OcrClient
    from alibabacloud_tea_openapi.models import Config

    ak, sk, endpoint = _creds()
    cfg = Config(ak=ak, secret=sk, endpoint=endpoint)
    return OcrClient(cfg)


def _resolve_input(image: str) -> tuple[str | None, bytes | None]:
    """返回 (url, body)。URL 形式给出 url；本地/字节给出 body。"""
    if image.startswith(("http://", "https://")):
        return image, None
    if image.startswith("data:"):
        raw = base64.b64decode(image.split(",", 1)[-1])
        return None, raw
    p = Path(image)
    if p.exists():
        return None, p.read_bytes()
    # 裸 base64 兜底
    try:
        return None, base64.b64decode(image, validate=False)
    except Exception as e:
        raise ValueError(f"无法解析 image 参数（既非存在路径，也非合法 URL/base64）：{e}") from e


@mcp.tool()
def recognize_text(image: str) -> str:
    """识别图片或 PDF 中的文字（中文为主），返回阿里云给出的 markdown 文本。

    适合：文档/截图/扫描件/PDF 的文字抽取。比把页面当图片丢给 Vision 更便宜、更适合 PDF。

    Args:
        image: 图片/PDF 来源，支持以下任一形式：
            - 本地文件路径（图片或 PDF）
            - http(s) URL
            - data: URI
            - 裸 base64 字符串
    """
    from alibabacloud_ocr_api20210707 import models as ocr_models

    url, body = _resolve_input(image)
    client = _client()
    req = ocr_models.RecognizeGeneralRequest(url=url, body=body)
    try:
        resp = client.recognize_general(req)
    except Exception as e:
        # 阿里云 Tea SDK 的错误对象通常带 .message / .code
        msg = getattr(e, "message", None) or str(e)
        code = getattr(e, "code", None)
        raise RuntimeError(f"阿里云 OCR 调用失败{f' [{code}]' if code else ''}: {msg}") from e

    data = getattr(resp.body, "data", None)
    if not data:
        return "未识别到文字（响应 data 为空）。"
    return data if isinstance(data, str) else str(data)


@mcp.tool()
def ocr_health() -> str:
    """检查 OCR 凭据是否已配置（不发请求，仅校验环境变量）。"""
    try:
        _creds()
        return "凭据已配置，OCR server 就绪。"
    except RuntimeError as e:
        return f"未就绪：{e}"


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
        mcp.settings.port = int(os.environ.get("MCP_PORT", "8001"))
        print(f"[ocr] streamable-http @ {mcp.settings.host}:{mcp.settings.port}", file=sys.stderr)
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
