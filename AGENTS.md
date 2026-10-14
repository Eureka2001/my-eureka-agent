# AGENTS.md — my-eureka-agent

个人 AI Agent 基础设施仓库：本地 MCP server、MCP 网关、ZCode skills 与插件清单。
Windows 专用个人环境，不为跨平台/多用户引入抽象。

## 环境与工具链

- 本机 Python 一律走 uv：`uv run` / `uv add` / `uv sync`，不找系统 Python。
- 每个 MCP server 一个独立 uv 项目（`mcp/<name>/`），依赖互相隔离；网关自身也
  是独立项目（`mcp/gateway/`），依赖仅 `mcp` SDK。
- 质量门（新 server 对齐 `mcp/habitica` 的标准）：ruff（E4/E7/E9/F/B/I/UP，
  88 列）+ mypy（`disallow_untyped_defs`）+ pytest，三者全绿才算完成。

## MCP 架构（改代码前必读）

- 各 Agent 客户端（ZCode / Codex / Claude Code）**不直连** server，统一走网关
  `eureka` @ `http://127.0.0.1:1820/mcp`。网关由计划任务 `eureka-gateway`
  常驻托管（登录自启 + 10 分钟看门狗 + 崩溃重启）。
- 网关聚合 `mcp/` 下全部 server 为单一入口：`tools/list` 走静态清单
  `mcp/gateway/tools.json`（零 spawn）；`tools/call` 按需 spawn 后端子进程、
  空闲 180s 回收、崩溃退避重启。
- **改网关代码前先读 `mcp/gateway/README.md` 的「架构约束」**（supervisor 独占
  生命周期、taskkill /T 杀树、count_death 记账、pythonw 日志约束）——这些是
  实测踩坑换来的，绕开会复发。
- **后端 server 增改工具后必须重生成清单**，否则网关看不到：
  `cd mcp/gateway && uv run scripts/dump_manifest.py`。
- 本地测试别占生产端口 1820：起测试实例用 `MCP_PORT` 换端口，或先
  `install-task.ps1 -Uninstall` 停掉常驻实例。

## 凭据

- 仓库零凭据；根目录 `.env`（gitignored）由各 server 的 dotenv 逻辑从
  `__file__` 向上查找到并加载。
- `HABITICA_*` 在用户级环境变量；网关经 `backends.env_for` 按前缀注入 habitica
  子进程（它自身不读 .env）。

## 运行与排障

- 网关唯一"控制台"是日志文件 `mcp/gateway/logs/gateway.log`
  （attach：`Get-Content -Wait`；后台启停/自启管理见 `mcp/gateway/README.md`）。
- 冒烟：`cd mcp/gateway && uv run scripts/smoke_http.py [--call qr_backends]`。
- 单独调试某个 server：`cd mcp/<name> && uv run server.py` 照旧可用。

## 维护规范

### 新后端接入契约

每个工具的双重身份——独立 MCP Server / 被网关整合——靠以下契约维持；
满足即只需在 `backends.py` 注册表加条目 + `uv run scripts/dump_manifest.py`，
不需要动网关代码：

1. 独立 uv 项目，可被 argv 直接启动（`server.py` 或 console-script exe）；
   独立运行能力不因接入而削弱，二者不共享状态。
2. 工具名在全部后端中全局唯一（dump 脚本撞名会直接失败，机器守卫）。
3. 凭据二选一：dotenv 从 `__file__` 向上查找 `.env`（推荐，零配置）；
   或在注册表声明 `env_prefixes` 由网关注入（如 habitica）。
4. 可被杀死与重启：不依赖致命的进程内会话状态、stdin EOF 时干净退出、
   工具尽量幂等——网关会空闲回收并可能在崩溃后重拉。
5. stdio 铁律：诊断只写 stderr，绝不写 stdout。

### 整合边界与已知限制

- 网关只代理 tools；提供 resources / prompts / 服务端 sampling 的 server
  不适用本方案，需单独评估。
- 进度通知（progress）不转发，最终结果完整送达。
- `GATEWAY_IDLE_TIMEOUT` / `GATEWAY_CALL_TIMEOUT` 目前全局一份；出现重会话
  状态型或长任务型工具时，再为其加 per-backend 覆盖（BackendSession 已预留
  构造参数，注册表尚未暴露）。

### 其他约定

- 命名：server 内部注册名 `eureka_` 前缀；客户端只见网关注册名 `eureka`
  （工具形如 `mcp__eureka__playwright_fetch`）。
- 客户端配置以根 `mcp.json` 为源，手动同步三处：ZCode
  （`~/.zcode/cli/config.json` 的 `mcp.servers` 嵌套键）、Codex
  （`~/.codex/config.toml`）、Claude Code（`~/.claude.json`）。
- 多步骤工作用 `.planning/<日期>-<主题>/` 三文件记录（task_plan / findings /
  progress，gitignored）；重大决策要能从那里追溯。
