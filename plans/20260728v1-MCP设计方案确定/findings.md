# 调研发现

> 仅记录外部检索结论。不可信网页内容只写本文件，不写 task_plan.md。

## 仓库现状
- 仓库定位：个人 Skills + MCP 源仓库；`skills/` 下已有 5 个自建 Skill。
- `mcp/` 目录为空，待建；README 明确凭据不入库，`.gitignore` 已屏蔽 `.env*`/`*key*`/`*token*`/`*secret*`/`credentials/`。
- 设计推论：MCP server 进程从环境变量读 API Key；仓库内只允许出现「占位/示例」，不出现真实凭据。

---

## 路线 A：MCP Python SDK + uv + transport（已完成）

### SDK 现状（2026-07）
- 官方包 `mcp`（Anthropic 维护），稳定版 **1.28.x**，Python ≥ 3.10；2.0 仍在 RC。**依赖加上界 `mcp>=1.27,<2`**。
- 用官方内置 `from mcp.server.fastmcp import FastMCP`（装饰器 `@mcp.tool()`），**不要**混用第三方独立 `fastmcp` 包。
- 最小 stdio server：`mcp.run(transport="stdio")`；改 HTTP 仅换 `transport="streamable-http"`。迁移成本约 5 行。
- 来源：[pypi.org/project/mcp](https://pypi.org/project/mcp/)、[github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

### transport 取舍
- **本地 Agent 兜底 → stdio**（无端口、无鉴权、进程隔离最干净）。
- 远程/多用户/需鉴权审计 → Streamable HTTP。
- 关键铁律：**stdio 模式下日志只能写 stderr/文件，绝不能写 stdout**（会污染协议流导致卡死）。
- 来源：[TrueFoundry](https://www.truefoundry.com/blog/mcp-stdio-vs-streamable-http-enterprise)、[Ginger Labs](https://gingerlabs.ai/blog/mcp-transport-comparison)

### uv 管理
- 三种形态：`uv run --with`（临时）/ PEP 723 单文件 / **独立项目 pyproject.toml**。
- 「每个 MCP server 一个独立 uv 项目」是官方 + 社区主流推荐。一文件小工具可用 PEP 723。
- 来源：[PyPI mcp](https://pypi.org/project/mcp/)、[CircleCI 教程](https://circleci.com/blog/building-and-deploying-a-python-mcp-server-with-fastmcp/)

### Windows 11 注意点（高频坑）
1. `command` 里别裸写 `npx`/`uvx`（是 `.cmd` 包装，spawn 报 CreateProcess error=193）；用 `cmd /c` 包一层或写绝对 `.cmd`/`.exe` 路径。
2. Python server 注册优先 `uv run --with mcp python /abs/path/server.py`。
3. 路径用绝对路径 + 双反斜杠；**路径含空格会破坏 MCP**。
4. 日志写 stderr。
5. 验证用 `npx -y @modelcontextprotocol/inspector`。
- 来源：[cline#902](https://github.com/cline/cline/issues/902)、[官方 Build Server](https://modelcontextprotocol.io/docs/develop/build-server)

### server 切分粒度
- 社区共识：**按领域聚合**，每个 server 内工具 ≤7 个；不要堆一个胖 server（工具>10 时 agent 选错率陡增），也不必每工具一 server。
- 来源：[HN: Big Lessons from MCP](https://news.ycombinator.com/item?id=44315151)、[官方 Architecture](https://modelcontextprotocol.io/docs/learn/architecture)

---

## 路线 B：cc-switch + 各客户端注册（已完成）

### ⚠️ 与原方案的两处重大冲突
1. **ChatGPT Work 不支持本地 stdio MCP**，只支持远程（SSE / Streamable HTTP）。来源：[OpenAI MCP 文档](https://developers.openai.com/api/docs/mcp)、[4sysops 实测](https://4sysops.com/archives/add-chatgpt-mcp-serveranother-setback-for-openai/)。
   → 想在 ChatGPT Work 用，必须把 server 跑成 HTTP（或用 mcp-remote/localtunnel 桥接）。
2. **cc-switch 的 MCP 同步只覆盖 5 个 CLI**（Claude Code / Codex / Gemini CLI / OpenCode / Hermes），**不能**注册到 ChatGPT Work、Qoder、Claude Desktop。
   → 「cc-switch 一次性注册所有 MCP 到 ChatGPT Work」这条路不成立。

### cc-switch 真实能力
- Tauri 桌面 All-in-One 管理器：①API Provider 切换 ②MCP server 管理。
- MCP 同步写入路径：Claude Code→`~/.claude.json`、Codex→`~/.codex/config.toml`、Gemini CLI→`~/.gemini/settings.json` 等。
- 已知坑：Issue [#2684](https://github.com/farion1231/cc-switch/issues/2684)/[#4645](https://github.com/farion1231/cc-switch/issues/4645) 反映同步偶发不生效/改写配置，需人工核对。
- 来源：[farion1231/cc-switch](https://github.com/farion1231/cc-switch)、[MCP 管理文档](https://github.com/farion1231/cc-switch/blob/main/docs/user-manual/zh/3-extensions/3.1-mcp.md)

### 各客户端 stdio MCP 配置
- **Claude Code**：`claude mcp add <name> -- <cmd> <args>`；project scope 写仓库根 `.mcp.json`。✅
- **Qoder / QoderWork**：Settings → Connectors & MCP → +Add → Paste JSON Config → Import；JSON 格式与 Claude Code 兼容。✅
- **ChatGPT Work**：仅远程 HTTP。❌（stdio）
- **WorkBuddy**：检索不到该名称的公开产品/MCP 文档，**无法验证**，需用户确认准确名称。

### 软链接（~/.mcp-servers）模式评估
- **非社区约定**，无既定标准；技术上可行但收益低。
- 坑：Windows symlink 需管理员/开发者模式；路径含空格破坏 MCP；增加 symlink 逃逸攻击面；各客户端不会自动扫描目录。
- **更优替代**：直接在客户端配置里引用仓库内绝对路径；如需稳定路径用 `mklink /J`（目录联接，Windows 无需管理员）。

### 跨设备同步现实做法
- 推荐：源码 + project 级 `.mcp.json`（凭据用 `${ENV_VAR}` 占位）进 git；各设备本地用系统级 secrets（Win Credential Manager / `.env`+direnv）注入凭据。
- 弊端：绝对路径跨平台冲突（Win `C:\` vs Mac `/`）；运行时依赖（uv/python 版本）各设备自理；GUI 客户端不读仓库 `.mcp.json`，需手工再配。

---

## 路线 C：4 项能力的现成方案（已完成）

### 网页抓取（含懒加载）
- 纯 httpx 拿不到 JS 渲染/海报 PNG 内容；单一抓取器兜不住。
- 推荐**分级 fallback**：① Jina Reader / Firecrawl（远程，对微信公众号优化好）② 本地 Playwright MCP（反爬/登录态/重 JS）③ 检测到正文只剩 `<img>` → 抽图走 OCR/VLM。
- Crawl4AI 官方原生 MCP 未落地，现有都是社区薄封装，**不推荐直接依赖**；要么用其 Docker API，要么用 Microsoft Playwright MCP。
- 来源：[microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)、[jina-ai/MCP](https://github.com/jina-ai/MCP)、[crawl4ai self-hosting](https://docs.crawl4ai.com/core/self-hosting/)

### OCR（中文）
- 本地：**RapidOCR**（基于 PaddleOCR 模型转 ONNX，pip 即用、无 Paddle 依赖，跨平台最稳）> PaddleOCR（强但 Windows 偶有坑）> Tesseract（中文弱，不推荐）。
- 云 API：阿里云/腾讯云/百度中文印刷体准确率几乎无差，选哪家看账号额度。阿里云用 `RecognizeGeneral`（注意区别于 `RecognizeAllText`），SDK `alibabacloud_ocr_api20210707`。
- 来源：[RapidOCR 文档](https://rapidai.github.io/RapidOCRDocs/main/)、[阿里云 OCR](https://help.aliyun.com/zh/ocr/developer-reference/api-ocr-api-2021-07-07-recognizegeneral)

### QR Code 解码
- **无生产级现成 MCP**（GitHub 上多为「生成」而非解码），自己实现最靠谱。
- 库选型：pyzbar（轻、多码，Windows 需 ZBar.dll）→ fallback **OpenCV WeChatQRCode**（工业级，模糊/倾斜/反光强，需 4 个模型文件）→ 极端情况丢 GLM-4.6V。
- 来源：[WeChatQRCode 示例](https://cloud.tencent.com/developer/news/2648316)

### 视觉理解（GLM-4.6V）
- `glm-4.6v`（高性能）/ `glm-4.6v-flashx`（轻量）/ `glm-4.6v-flash`（**免费**）；128K 上下文，原生 Function Call。
- Endpoint `POST https://open.bigmodel.cn/api/paas/v4/chat/completions`，`Authorization: Bearer <key>`；`image_url.url` 支持公网 URL 或**裸 base64**。
- SDK：新 `zai-sdk`（`pip install zai-sdk`，`from zai import ZhipuAiClient`）或旧 `zhipuai>=2.1.5`。
- 来源：[GLM-4.6V 文档](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-4.6v)

### 🔑 关键认知（用户判断，已采纳）
三个能力是**互补关系，并非 vision 吞噬 OCR/QR**，各有不可替代的价值：
- **QR 解码**：需要确定性、可靠的结果，VLM 不可作为替代（会幻觉、不可复现）。
- **OCR（文字识别）**：**更便宜**，且适合处理 **PDF 文件**——PDF 的文字抽取用 OCR 远比把每页当图片丢给 Vision 合适（成本、速度、准确率都更优）。
- **Vision（视觉理解）**：用于真正的「看图理解」场景（海报、图表、场景图等），不是 OCR/QR 的上位替代。

→ 设计取向：**三者并列，按场景分工**。Vision 不作为主轴去吸收另两者。
