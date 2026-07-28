"""视觉理解 MCP server —— GLM-4.6V / Qwen-VL 双后端。

定位：真正的「看图理解」（海报、图表、场景图、UI 截图等）。**不**用来替代 OCR（文档/PDF 文字
抽取用 ocr server，更便宜）或 qrcode（确定性解码）。

两家均提供 OpenAI 兼容端点，统一用 openai SDK 调用，由环境变量切换后端：
  VISION_BACKEND       glm（默认）| qwen
  GLM_API_KEY          智谱 API key（glm-4.6v；可用 GLM_VISION_MODEL 指定 flash 等）
  DASHSCOPE_API_KEY    阿里 DashScope key（qwen-vl-max；可用 QWEN_VISION_MODEL 指定）

transport 双模：默认 stdio；MCP_TRANSPORT=http 或 --http 走 streamable-http。
诊断信息只写 stderr。
"""

from __future__ import annotations

import base64
import mimetypes
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vision")

_BACKENDS = ("glm", "qwen")


def _backend_config(name: str | None) -> tuple[str, str, str, str]:
    """返回 (backend, api_key, base_url, model)。"""
    name = (name or os.environ.get("VISION_BACKEND", "glm")).lower()
    if name in ("qwen", "qwen-vl", "dashscope"):
        key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY", "")
        base = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = os.environ.get("QWEN_VISION_MODEL", "qwen-vl-max")
        name = "qwen"
    elif name == "glm":
        key = os.environ.get("GLM_API_KEY", "")
        base = os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        model = os.environ.get("GLM_VISION_MODEL", "glm-4.6v")
    else:
        raise ValueError(f"未知 backend: {name}（支持 {_BACKENDS}）")

    if not key:
        env_hint = "GLM_API_KEY" if name == "glm" else "DASHSCOPE_API_KEY"
        raise RuntimeError(f"缺少 {name} 的 API key，请设置环境变量 {env_hint}")
    return name, key, base, model


def _image_block(image: str) -> dict:
    """把图片来源归一化为 OpenAI vision 的 image_url 内容块。"""
    if image.startswith(("http://", "https://", "data:")):
        url = image
    else:
        p = Path(image)
        if p.exists():
            mime = mimetypes.guess_type(p.name)[0] or "image/png"
            b64 = base64.b64encode(p.read_bytes()).decode()
            url = f"data:{mime};base64,{b64}"
        else:
            # 当作裸 base64
            url = f"data:image/png;base64,{image}"
    return {"type": "image_url", "image_url": {"url": url}}


@mcp.tool()
def understand_image(
    image: str,
    prompt: str = "请详细、准确地描述这张图片的内容。",
    backend: str = "",
) -> str:
    """用多模态大模型理解图片，返回文字描述或对 prompt 的回答。

    适用：海报、图表、场景图、UI 截图等需要「语义理解」的场景。
    文档/PDF 文字抽取请用 ocr server（更便宜）；二维码解码请用 qrcode server（确定性）。

    Args:
        image: 图片来源：本地路径 / http(s) URL / data: URI / 裸 base64。
        prompt: 想让模型回答的问题或指令，默认「描述图片内容」。
        backend: glm 或 qwen；留空则读环境变量 VISION_BACKEND（默认 glm）。
    """
    from openai import OpenAI

    name, key, base, model = _backend_config(backend or None)
    client = OpenAI(api_key=key, base_url=base)
    messages = [
        {
            "role": "user",
            "content": [_image_block(image), {"type": "text", "text": prompt}],
        }
    ]
    try:
        resp = client.chat.completions.create(model=model, messages=messages)
    except Exception as e:
        raise RuntimeError(f"[{name}/{model}] 视觉模型调用失败: {e}") from e
    return (resp.choices[0].message.content or "").strip() or "(模型返回为空)"


@mcp.tool()
def vision_health() -> str:
    """报告当前默认后端的配置状态（不发请求）。"""
    try:
        name, _key, base, model = _backend_config(None)
        return f"默认后端：{name}（{model} @ {base}），凭据已配置，vision server 就绪。"
    except (RuntimeError, ValueError) as e:
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
        mcp.settings.port = int(os.environ.get("MCP_PORT", "8002"))
        print(f"[vision] streamable-http @ {mcp.settings.host}:{mcp.settings.port}", file=sys.stderr)
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
