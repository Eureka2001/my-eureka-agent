# mcp-fetch

网页抓取 MCP server。**Playwright 渲染**，支持 JS 渲染与懒加载（滚动触发），输出 markdown。

## 工具

| 工具 | 作用 |
|---|---|
| `playwright_fetch(url, wait_seconds?, scroll_to_load?, max_chars?, precise_sizes?)` | 无头浏览器抓取渲染后页面，返回 markdown 正文 + 末尾「图片清单」（客观元数据：分辨率/显示尺寸/字节数/alt/URL，已过滤装饰图标）。 |
| `fetch_health()` | 检查 chromium 内核是否已安装。 |

`playwright_fetch` 的图片清单只含**客观信息**，不做角色推断。是否值得送 OCR/Vision/QR 由上游根据尺寸+alt 自行判断；「图表 vs 照片」需配合 vision。字节数默认取浏览器响应的 `Content-Length`（拿不到显示 `?`）；`precise_sizes=True` 时对缺失项用 httpx 实测（更准但更慢）。图片 URL 可直接喂给 `eureka_ocr` / `eureka_vision` / `eureka_qrcode` server，无需单独下载。

## 首次安装（一次性）

```bash
cd mcp/fetch
uv sync
uv run playwright install chromium   # 下载浏览器内核
```

## 运行

```bash
uv run server.py            # stdio
uv run server.py --http     # streamable-http（默认 127.0.0.1:8003）
```
`MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT` 同其它 server。

## 注册到客户端

### Claude Code
```json
{
  "mcpServers": {
    "eureka_fetch": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "D:/Repositories/my-eureka-agent/mcp/fetch", "server.py"]
    }
  }
}
```
Qoder 粘贴同款 JSON；ChatGPT Work 需 HTTP 常驻进程再以 URL 添加。本 server 无凭据。

## 说明
- `max_chars` 默认 20000，防止大页面撑爆上下文。
- 部分强反爬站点（Cloudflare 等）可能仍失败——可后续按需加代理/UA 策略。
