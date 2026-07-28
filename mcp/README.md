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

三者非替代关系：解码→qrcode，PDF/文档文字→ocr，图像语义理解→vision，网页→fetch。

## 统一约定

- **transport 双模**：默认 stdio；`MCP_TRANSPORT=http` 或 `--http` 走 streamable-http（HTTP 模式端口：qrcode 8000 / ocr 8001 / vision 8002 / fetch 8003）。
- **stdio 铁律**：诊断信息只写 stderr，绝不写 stdout。
- **运行**：`cd <server> && uv run server.py`；fetch 首次需 `uv run playwright install chromium`。

## 路径方案（已确认：Windows 目录联接）

如需把仓库路径解耦到稳定位置，用**目录联接**（无需管理员权限）：

```cmd
mklink /J "%USERPROFILE%\.mcp-servers\qrcode" "D:\Repositories\my-eureka-agent\mcp\qrcode"
```

> 不要用 symlink（需管理员）。

## 注册矩阵

| 客户端 | transport | 方式 |
|---|---|---|
| Claude Code / Codex / Gemini CLI / OpenCode | stdio | cc-switch 批量写入；或各 server README 的 `claude mcp add` |
| Qoder / QoderWork | stdio | Settings → Connectors & MCP → 粘贴各 server README 的 JSON |
| ChatGPT Work | http（必须远程） | 各 server 以 HTTP 常驻进程，再以 `http://127.0.0.1:<port>/mcp` 添加 |

各 server 的具体注册 JSON 片段见对应子目录 README。
