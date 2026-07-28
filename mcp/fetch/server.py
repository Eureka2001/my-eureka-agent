"""网页抓取 MCP server —— Playwright 渲染。

定位：「极其稳定可靠」的网页获取，支持 JS 渲染与延迟加载（滚动触发懒加载）。
HTML → markdown 输出，便于上游 agent 阅读；末尾附「图片清单」（客观元数据），
供上游决定哪些图值得 OCR/Vision/QR。

首次使用需安装浏览器内核（一次性）：
    uv run playwright install chromium

transport 双模：默认 stdio；MCP_TRANSPORT=http 或 --http 走 streamable-http。
诊断信息只写 stderr。
"""

from __future__ import annotations

import os
import sys

import html2text
import markdownify
from readability import Document
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fetch")

# html2text 配置：保留链接与图片 URL（图片 URL 是上游决定是否 OCR/Vision/QR 的关键线索）
_H2T = html2text.HTML2Text()
_H2T.ignore_links = False
_H2T.ignore_images = False
_H2T.body_width = 0  # 不强制换行


def _html_to_markdown(html: str, use_readability: bool = False) -> str:
    if use_readability:
        try:
            cleaned_html = Document(html).summary()
            if cleaned_html:
                md = markdownify.markdownify(cleaned_html, heading_style=markdownify.ATX)
            else:
                md = _H2T.handle(html)  # fallback
        except Exception:
            md = _H2T.handle(html)  # fallback
    else:
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


async def _resolve_sizes(urls: list[str]) -> dict[str, int | None]:
    """对未从浏览器响应拿到 Content-Length 的图，用 httpx 兜底取字节数。

    HEAD 取不到则流式 GET 计数（上限 5MB，防超大文件）。
    """
    import httpx

    out: dict[str, int | None] = {}
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 mcp-fetch"}
    ) as c:
        for u in urls:
            sz: int | None = None
            try:
                r = await c.head(u)
                cl = r.headers.get("content-length")
                if cl and cl.isdigit():
                    sz = int(cl)
            except Exception:
                pass
            if sz is None:
                try:
                    n = 0
                    async with c.stream("GET", u) as r:
                        cl = r.headers.get("content-length")
                        if cl and cl.isdigit():
                            sz = int(cl)
                        else:
                            async for chunk in r.aiter_raw():
                                n += len(chunk)
                                if n > 5_000_000:
                                    break
                            sz = n
                except Exception:
                    pass
            out[u] = sz
    return out


def _human_bytes(n: int | None) -> str:
    if n is None:
        return "?"
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n/1024:.0f}KB"
    return f"{n/1024/1024:.1f}MB"


_IMG_JS = (
    "() => Array.from(document.querySelectorAll('img')).map(e => ({"
    " src: e.currentSrc || e.src || e.getAttribute('data-src') || '',"
    " nw: e.naturalWidth, nh: e.naturalHeight,"
    " w: e.width, h: e.height, alt: (e.alt || '').slice(0, 60)"
    "}))"
)


async def _collect(url: str, wait_seconds: float, scroll_to_load: bool):
    """渲染页面，返回 (html, img 元素列表, url→Content-Length 字节数)。"""
    from playwright.async_api import async_playwright

    sizes: dict[str, int | None] = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        def _on_resp(resp):
            try:
                if resp.request.resource_type == "image":
                    cl = resp.headers.get("content-length") or resp.headers.get("Content-Length")
                    sizes[resp.url] = int(cl) if (cl and cl.isdigit()) else None
            except Exception:
                pass

        page.on("response", _on_resp)
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        try:
            await page.wait_for_load_state("networkidle", timeout=int(wait_seconds * 1000))
        except Exception:
            pass
        await page.wait_for_timeout(int(wait_seconds * 1000))

        if scroll_to_load:
            last = -1
            for _ in range(12):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.8)")
                await page.wait_for_timeout(600)
                h = await page.evaluate("document.body.scrollHeight")
                if h == last:
                    break
                last = h
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(400)

        html = await page.content()
        raw_imgs = await page.eval_on_selector_all("img", _IMG_JS)
        await browser.close()
    return html, raw_imgs, sizes


def _dedupe_imgs(raw_imgs: list[dict]) -> dict[str, dict]:
    """按 URL 去重（取最大分辨率），剔除空 src 与 data: URI。"""
    best: dict[str, dict] = {}
    for e in raw_imgs:
        src = (e.get("src") or "").strip()
        if not src or src.startswith("data:"):
            continue
        nw, nh = e.get("nw", 0), e.get("nh", 0)
        prev = best.get(src)
        if prev is None or (nw * nh) > (prev["nw"] * prev["nh"]):
            best[src] = e
    return best


@mcp.tool()
async def fetch_url(
    url: str,
    wait_seconds: float = 2.0,
    scroll_to_load: bool = True,
    max_chars: int = 20000,
    start_index: int = 0,
    precise_sizes: bool = False,
    min_short_side: int = 100,
    use_readability: bool = True,
) -> str:
    """用无头浏览器抓取并渲染网页，返回 markdown 正文；末尾附「图片清单」。

    图片清单只含**客观信息**：分辨率、显示尺寸、字节数、alt、URL（已去重、过滤
    短边小于 min_short_side 的图标/装饰与 data URI）。

    Args:
        url: 目标网页地址。
        wait_seconds: 首屏后额外等待秒数，给 JS/网络完成留时间。
        scroll_to_load: 是否逐屏滚动以触发懒加载内容。
        max_chars: 返回（正文+清单）总字符上限。
        start_index: 从第几个字符开始返回（用于分页续读上次被截断的内容）。
        precise_sizes: 为 True 时，对未暴露 Content-Length 的图用 httpx 实测字节数（更准但更慢，一般并无必要）。
        min_short_side: 图片短边最小像素阈值，短边小于此值的图视为图标/装饰而被过滤，默认 100。
        use_readability: 为 True 时，用 Readability 算法先提取正文区域再转 markdown（去噪更好，适合文章页；对复杂布局页面可能误判，此时建议关闭）。
    """
    html, raw_imgs, sizes = await _collect(url, wait_seconds, scroll_to_load)
    md = _html_to_markdown(html, use_readability=use_readability)

    # 构建图片清单（过滤短边<min_short_side 的图标/装饰；保留 0x0 未加载项以提示上游）
    best = _dedupe_imgs(raw_imgs)
    content = {
        s: e
        for s, e in best.items()
        if not (min(e.get("nw", 0), e.get("nh", 0)) and min(e.get("nw", 0), e.get("nh", 0)) < min_short_side)
    }
    if precise_sizes and content:
        missing = [s for s in content if sizes.get(s) is None]
        if missing:
            sizes.update(await _resolve_sizes(missing))

    if content:
        lines = ["", "## 图片清单（客观元数据，已过滤装饰/图标）", ""]
        for s, e in content.items():
            nw, nh = e.get("nw", 0), e.get("nh", 0)
            disp = f"{e.get('w')}x{e.get('h')}" if e.get("w") and e.get("h") else "?"
            alt = e.get("alt", "")
            lines.append(
                f"- {nw}x{nh}（显示 {disp}） {_human_bytes(sizes.get(s))} alt=\"{alt}\" {s}"
            )
        md = md.rstrip() + "\n" + "\n".join(lines)

    total = len(md)
    if start_index >= total:
        return "<error>没有更多内容了（start_index 已超出总字符数）</error>"
    md = md[start_index:]
    if len(md) > max_chars:
        next_start = start_index + max_chars
        md = md[:max_chars] + f"\n\n…（已截断，共 {total} 字符，本次返回 {start_index}~{start_index + max_chars}。如需继续，请传 start_index={next_start}）"
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
