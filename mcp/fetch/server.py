"""网页抓取 MCP server —— Playwright 渲染。

定位：「极其稳定可靠」的网页获取，支持 JS 渲染与延迟加载（滚动触发懒加载）。
HTML → markdown 输出，便于上游 agent 阅读。

首次使用需安装浏览器内核（一次性）：
    uv run playwright install chromium

transport 双模：默认 stdio；MCP_TRANSPORT=http 或 --http 走 streamable-http。
诊断信息只写 stderr。
"""

from __future__ import annotations

import os
import sys

import html2text
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fetch")

# html2text 配置：保留链接、适度精简
_H2T = html2text.HTML2Text()
_H2T.ignore_links = False
_H2T.ignore_images = True
_H2T.body_width = 0  # 不强制换行


def _html_to_markdown(html: str) -> str:
    md = _H2T.handle(html)
    # 折叠多余空行
    lines = [ln.rstrip() for ln in md.splitlines()]
    out: list[str] = []
    blank = False
    for ln in lines:
        if ln == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip()


@mcp.tool()
async def fetch_url(
    url: str,
    wait_seconds: float = 2.0,
    scroll_to_load: bool = True,
    max_chars: int = 20000,
) -> str:
    """用无头浏览器抓取并渲染网页，返回 markdown 正文。支持 JS 渲染与懒加载。

    Args:
        url: 目标网页地址。
        wait_seconds: 首屏后额外等待秒数，给 JS/网络完成留时间。
        scroll_to_load: 是否逐屏滚动以触发懒加载内容。
        max_chars: 返回 markdown 的最大字符数（截断，避免上下文爆炸）。
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            # 等网络空闲（最多等 wait_seconds）
            try:
                await page.wait_for_load_state("networkidle", timeout=int(wait_seconds * 1000))
            except Exception:
                pass  # 部分站点持续有网络活动，超时即继续
            await page.wait_for_timeout(int(wait_seconds * 1000))

            if scroll_to_load:
                last = -1
                for _ in range(12):  # 最多滚 12 屏
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.8)")
                    await page.wait_for_timeout(600)
                    h = await page.evaluate("document.body.scrollHeight")
                    if h == last:
                        break
                    last = h
                await page.evaluate("window.scrollTo(0, 0)")

            html = await page.content()
        finally:
            await browser.close()

    md = _html_to_markdown(html)
    if len(md) > max_chars:
        md = md[:max_chars] + f"\n\n…（已截断，共 {len(md)} 字符，仅返回前 {max_chars}）"
    return md or "(抓取到的页面内容为空)"


@mcp.tool()
async def fetch_health() -> str:
    """检查 Playwright chromium 内核是否已安装。"""
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(headless=True)
            await b.close()
        return "Playwright chromium 就绪，fetch server 可用。"
    except Exception as e:
        return (
            "chromium 未就绪：请先执行 `uv run playwright install chromium`。\n"
            f"详情: {e}"
        )


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
        mcp.settings.port = int(os.environ.get("MCP_PORT", "8003"))
        print(f"[fetch] streamable-http @ {mcp.settings.host}:{mcp.settings.port}", file=sys.stderr)
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
