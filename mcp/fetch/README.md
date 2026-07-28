# mcp-fetch

网页抓取 MCP server。**Playwright 渲染**，支持 JS 渲染与懒加载（滚动触发），输出 markdown。

## 工具

| 工具 | 作用 |
|---|---|
| `fetch_url(url, wait_seconds?, scroll_to_load?, max_chars?)` | 无头浏览器抓取渲染后页面，返回 markdown。 |
| `fetch_health()` | 检查 chromium 内核是否已安装。 |

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
    "fetch": {
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
