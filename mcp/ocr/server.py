"""OCR MCP server —— 阿里云通用文字识别。

定位：**更便宜、适合 PDF/文档文字抽取**（PDF 用 OCR 远优于逐页丢给 Vision）。
后端：阿里云 ocr-api 服务的「统一识别」RecognizeAllText（官方推荐，支持图片与 PDF）。

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


def _bootstrap_env() -> None:
    """启动时向上查找最近的 .env（server 目录或仓库根）并加载。

    override=False：客户端在配置里显式注入的同名变量优先于 .env。
    """
    try:
        from dotenv import load_dotenv
    except Exception:  # python-dotenv 未装则跳过（凭据可由客户端 env 提供）
        return
    for d in Path(__file__).resolve().parents:
        if (d / ".env").exists():
            load_dotenv(d / ".env", override=False)
            return


_bootstrap_env()


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
    cfg = Config(access_key_id=ak, access_key_secret=sk, endpoint=endpoint)
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


def _extract_text(data) -> str:
    """从 RecognizeAllText 的 data 里抽取文字。

    阿里云 SDK 可能将 data 返回为 JSON 字符串、Python repr 或原生 dict/list。
    逐层尝试：字符串 → 解析为结构体 → 找语义键 → 兜底原文。
    """
    import ast, json

    if data is None:
        return ""
    # 字符串：尝试反序列化为 dict/list（JSON 或 Python repr 都可能出现）
    if isinstance(data, str):
        parsed = data
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(data)
            except Exception:
                pass
            else:
                if isinstance(parsed, (dict, list)):
                    return _extract_text(parsed)
        return parsed  # 无法解析则返回原文
    if isinstance(data, (list, tuple)):
        return "\n".join(_extract_text(x) for x in data if x is not None).strip()
    if isinstance(data, dict):
        # 优先取顶层语义键（阿里云 RecognizeAllText 返回 Content 为聚合全文）
        for k in ("Content", "content", "text", "markdown", "result", "data", "words"):
            if k in data:
                t = _extract_text(data[k])
                if t:
                    return t
        return json.dumps(data, ensure_ascii=False)
    # Tea SDK 模型对象：to_map() → dict
    if hasattr(data, "to_map"):
        try:
            return _extract_text(data.to_map())
        except Exception:
            pass
    return str(data)


@mcp.tool()
def recognize_text(image: str) -> str:
    """识别图片或 PDF 中的文字（中文为主），返回阿里云「统一识别」给出的文本。

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
    # 「统一识别 RecognizeAllText」——阿里云官方推荐的新接口，支持图片与 PDF。
    # Type="Advanced" 为通用高级识别，覆盖图片与 PDF 文字抽取。
    req = ocr_models.RecognizeAllTextRequest(url=url, body=body, type="Advanced")
    try:
        resp = client.recognize_all_text(req)
    except Exception as e:
        # 阿里云 Tea SDK 的错误对象通常带 .message / .code
        msg = getattr(e, "message", None) or str(e)
        code = getattr(e, "code", None)
        raise RuntimeError(f"阿里云 OCR 调用失败{f' [{code}]' if code else ''}: {msg}") from e

    text = _extract_text(getattr(resp.body, "data", None))
    return text or "未识别到文字（响应 data 为空）。"


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
