# mcp/ —— 本地 MCP 工具集

给各 AI Agent（Claude Code / Qoder / ChatGPT Work 等）做能力兜底的本地 MCP server。
每个 server 一个独立 uv 项目，依赖隔离；凭据全部走环境变量（仓库零凭据）。

## 能力分工（并列，按场景选）

| server | 定位 | 主后端 | 凭据 env |
|---|---|---|---|
| `qrcode/` | 确定性 QR/条码解码（VLM 不可替代） | pyzbar → wechat-qrcode | 无 |
| `ocr/` | 图片/PDF 文字识别（便宜、适合 PDF） | 阿里云 RecognizeGeneral | `ALIYUN_OCR_AK_ID` / `ALIYUN_OCR_AK_SECRET` |
| `vision/` | 图像语义理解（海报/图表/场景） | GLM-4.6V 或 Qwen-VL（env 切换） | `GLM_API_KEY` / `DASHSCOPE_API_KEY` |
| `fetch/` | 网页抓取（JS 渲染、懒加载） | Playwright | 无 |
| `mcp_server_askecho_search_infinity/` | 联网搜索（结构化结果、权威分级） | 火山引擎豆包搜索 API | `ASK_ECHO_SEARCH_INFINITY_API_KEY` 或 `VOLCENGINE_ACCESS_KEY`/`VOLCENGINE_SECRET_KEY` |

四者非替代关系：解码→qrcode，PDF/文档文字→ocr，图像语义理解→vision，网页→fetch，联网搜索→search。

> `mcp_server_askecho_search_infinity/` 从 `volcengine/mcp-server` 官方仓库 sparse-checkout 同步，
> 仅取搜索子目录，不拉整个 monorepo。详见子目录 README。

## 统一约定

- **transport 双模**：默认 stdio；`MCP_TRANSPORT=http` 或 `--http` 走 streamable-http。
- **stdio 铁律**：诊断信息只写 stderr，绝不写 stdout。
- **运行**：`cd <server> && uv run server.py`（search 用 `uv run mcp-server-askecho-search-infinity`）；fetch 首次需 `uv run playwright install chromium`。
