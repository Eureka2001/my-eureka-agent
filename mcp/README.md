# mcp/ —— 本地 MCP 工具集

给各 AI Agent（Claude Code / Qoder / ChatGPT Work 等）做能力兜底的本地 MCP server。
每个 server 一个独立 uv 项目，依赖隔离；凭据全部走环境变量（仓库零凭据）。

## 接入方式：网关 HTTP 常驻

各 Agent 客户端指向网关的 HTTP 端点（仓库根 `mcp.json` 为源文件）：

```json
"eureka": {
  "type": "http",
  "url": "http://127.0.0.1:1820/mcp"
}
```

（Codex 的 TOML 形式：`[mcp_servers.eureka]` + `url = "http://127.0.0.1:1820/mcp"`。）

网关需先于客户端会话启动，后台启动/看日志/停止的一条命令见 `gateway/README.md`
的「后台常驻」一节。网关把下列全部 server 聚合为 `mcp__eureka__*` 工具：后端
按需 spawn、空闲 180s 回收、崩溃自动重启。单独调试某个 server 时仍可按老方式
`cd <server> && uv run server.py` 直挂（或网关跑 stdio 形态）。

## 能力分工（并列，按场景选）

| server | 定位 | 主后端 | 凭据 env |
|---|---|---|---|
| `qrcode/` | 确定性 QR/条码解码（VLM 不可替代） | pyzbar → wechat-qrcode | 无 |
| `ocr/` | 图片/PDF 文字识别（便宜、适合 PDF） | 阿里云 RecognizeGeneral | `ALIYUN_OCR_AK_ID` / `ALIYUN_OCR_AK_SECRET` |
| `vision/` | 图像语义理解（海报/图表/场景） | GLM-4.6V 或 Qwen-VL（env 切换） | `GLM_API_KEY` / `DASHSCOPE_API_KEY` |
| `fetch/` | 网页抓取（JS 渲染、懒加载） | Playwright | 无 |
| `habitica/` | Habitica 账户、任务、打卡、清单和标签（仅 STDIO） | Habitica 官方 API / FastMCP | `HABITICA_USER_ID` / `HABITICA_API_TOKEN` |
| `mcp_server_askecho_search_infinity/` | 联网搜索（结构化结果、权威分级） | 火山引擎豆包搜索 API | `ASK_ECHO_SEARCH_INFINITY_API_KEY` 或 `VOLCENGINE_ACCESS_KEY`/`VOLCENGINE_SECRET_KEY` |

四者非替代关系：解码→eureka_qrcode，PDF/文档文字→eureka_ocr，图像语义理解→eureka_vision，网页→eureka_fetch，联网搜索→eureka_search。

> `mcp_server_askecho_search_infinity/` 从 `volcengine/mcp-server` 官方仓库 sparse-checkout 同步，
> 仅取搜索子目录，不拉整个 monorepo。详见子目录 README。

## 统一约定

- **transport**：默认 stdio；原有通用服务支持 `MCP_TRANSPORT=http` 或 `--http` 走 streamable-http，`habitica/` 按使用需求仅支持 STDIO。
- **stdio 铁律**：诊断信息只写 stderr，绝不写 stdout。
- **运行**：`cd <server> && uv run server.py`（search 用 `uv run mcp-server-askecho-search-infinity`）；fetch 首次需 `uv run playwright install chromium`。
- **MCP 命名**：客户端统一注册名为 `eureka`（网关，工具形如 `mcp__eureka__playwright_fetch`）；server 内部注册名保留 `eureka_` 前缀（`eureka_fetch` / `eureka_ocr` / `eureka_qrcode` / `eureka_vision` / `eureka_search` / `eureka_habitica`），工具名保留描述性原名（如 `doubao_search`、`playwright_fetch`）。
