# 进度日志

## Session 1 — 2026-07-28
- 读取 TASK.md，明确需求：4 个本地 MCP 兜底工具 + 软链接 + cc-switch 注册，需可行性评估。
- 盘点仓库：`mcp/` 空；`skills/` 已有 5 个 Skill；README 有严格凭据约束。
- 启动 3 个后台调研 agent（MCP/uv、cc-switch/注册、4 项能力方案）。
- 建立规划三件套：task_plan.md / findings.md / progress.md。
- 三路后台调研全部返回，结论写入 findings.md。
- 关键冲突发现：① ChatGPT Work 不支持本地 stdio MCP（只支持远程 HTTP）；② cc-switch 的 MCP 同步只覆盖 5 个 CLI，覆盖不到 ChatGPT Work/Qoder。
- 产出 DESIGN.md（逐条裁决 + 推荐架构：4 个独立 uv server、双模 transport、vision 作主轴）。
- 阶段 1–4 完成；进入阶段 5，等待用户确认 4 个决策点。
- 用户确认：双模代码但只实测 stdio；OCR 只做云 API；4 个独立 server；首个实现 qrcode。
- 实现 `mcp/qrcode/`（pyproject.toml + server.py + README + .gitignore）：
  - 双模 transport（stdio 默认 / --http 或 MCP_TRANSPORT=http）；日志只写 stderr。
  - 后端：pyzbar → wechat-qrcode fallback；均优雅降级。
  - 冒烟测试通过：stdio 握手 OK；`qr_backends` 返回（本机 pyzbar 就绪）；`decode_qrcode` 端到端解码 QR→URL 成功。
- 链路已打通：FastMCP + uv + env + Windows。下一步可按 vision → fetch → ocr 顺序继续。
- 选型最终确定：OCR=阿里云 RecognizeGeneral；Vision=GLM-4.6V+Qwen-VL 双后端 env 切换（走 OpenAI 兼容端点）；fetch=仅 Playwright 单接口（用户改主意，不留双接口）；路径用 mklink /J。
- 实现 ocr server：阿里云 RecognizeGeneral（图片+PDF），env 凭据守卫，双模。冒烟通过（health 正确报缺凭据）。
- 实现 vision server：GLM/Qwen 双后端 env 切换，统一 openai SDK。冒烟通过（health 正确报缺 key）。
- 实现 fetch server：Playwright 单工具 + html2text，双模。依赖装好，工具注册验证通过；chromium 内核下载中（网络慢，后台 bmnjhh05l），真实抓取测试待内核就绪。
- 写 mcp/README.md 总览（分工表 + 双模约定 + mklink/J + 注册矩阵）。
- chromium 下载完成（exit 0）。
- 修复 fetch：FastMCP 在 asyncio 循环内运行，Playwright Sync API 不可用 → 改用 async API（`async_playwright` + `async def` 工具）。
- fetch 真实抓取测试通过：① example.com 静态页 → markdown；② quotes.toscrape.com/js（JS 渲染必需）→ 成功拿到 JS 加载的引言内容，scroll_to_load 触发懒加载、max_chars 截断均正常。
- 四个 server 全部实现并验证完成（ocr/vision 真实调用待用户提供 key；qrcode/fetch 已端到端实测）。
