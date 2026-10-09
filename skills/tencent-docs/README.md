# 本地 Fork 说明

本目录是腾讯文档官方 skill 的**本地改造版**，不是原版。改造动机、内容与维护方式见下文。

## 原始信息源

- 厂商 skill 分发包（CDN zip）：`https://cdn.addon.tencentsuite.com/static/tencent-docs.zip`
- MCP 端点（单一，全部工具由此暴露）：`https://docs.qq.com/openapi/mcp`
- 授权 / token 申请页：`https://docs.qq.com/scenario/open-claw.html?nlc=1`
- 基线：厂商版本 1.0.41；原版入库 commit `0a23f70`（feat: 添加 `tencent-docs` 官方原版并格式清洗）；改造日期 2026-10-09

## 为什么要改造

1. **架构不符**：官方 skill 按「mcporter + 4 个独立 MCP 服务（tencent-docs / slide-mcp / doc-mcp / sheet-mcp）」的架构编写；实测单一端点 `openapi/mcp` 已直接暴露全部约 225 个工具（`manage.*` / `doc.*` / `sheet.*` / `smartsheet.*` / `smartcanvas.*` / `slide_*` 等），独立引擎端点与 mcporter 均非必需。
2. **冗余且会静默漂移**：原版约 60%（317KB / 529KB）的文档是逐工具 API 手册，与 MCP 实时返回的 Schema 完全重复（实测 225/225 工具描述、1126/1126 参数说明、225/225 outputSchema 全覆盖），且会随服务端演进而**静默漂移**——这是保留原版最大的风险面。

## 改造内容

**删除（API 参考层 + mcporter 安装路径）：**

- `references/docengine_references.md`（101KB）、`references/slideengine_references.md`（95KB）、`sheet/api/mcp-api.md`（56KB）——逐工具 API 手册，由会话内 `tools/list` 实时 Schema 取代
- `references/auth.md`、`setup.sh`——mcporter OAuth 安装路径（本 fork 不经 mcporter 部署）
- `references/manage_references.md`、`references/smartsheet_references.md` 原地瘦身：只留「动作 → 工具」地图、概念模型、枚举值、字段值格式、典型工作流

**改写（去 mcporter 化 / 客户端无关化）：**

- `SKILL.md`：快速配置 / 调用方式 / 错误码 / 排查步骤 / 更新策略，全部指向单一 MCP 端点与实时 Schema；工具命名统一为"以当前会话实际暴露的为准"
- `slide/entry.md`、`sheet/entry.md`：去服务绑定表述；脚本内批量调用改为 MCP HTTP 端点直连
- `references/workflows.md`、`references/aipage_references.md`、`sidebar-pptx-generator/references/design-principle.md`：修正指向已删文件的引用与 mcporter 调用示例

**脚本层移植（二次修复）：** 原脚本的 `mcporter` 调用全部移除——新增共享封装 `mcp_call.js`（Node 零依赖直连 MCP HTTP 端点，自动解 JSON-RPC / SSE 信封，CLI 与 require 双模式）；`get_slide_info` 状态脚本由 bash + jq + mcporter 重写为纯 Node（`get_slide_info.js`）；`import_file.sh`、`ocr.js` 改走 `mcp_call.js`。脚本依赖收敛为 **Node.js (>= 14) + curl + 环境变量 `TENCENT_DOCS_TOKEN`**。

**保留不动：** 场景路由表、四份品类 `entry.md` 工作流、MDX / JSX 组件 / DESIGN 规范、模板、全部本地脚本（`aipage_pack.js` / `import_file.sh` / `ocr.js` / `sidebar-pptx-generator/scripts/`）。

## 更新策略

1. 用 `check_skill_update` 工具盯版本：**只信返回中的 `latest` 与 `release_note` 字段**——`instruction` 字段实测无论传什么版本都恒定输出「需要更新」，服务端不做版本比较，无参考价值
2. `latest` 大于 SKILL.md frontmatter `version` 时，从上方 CDN zip 下载原包，diff 对应品类的 `entry.md` / `references/`，把**工作流层**的更新手工搬进本 fork
3. **禁止**用厂商 zip 整包覆盖本目录（会冲掉瘦身改动）；**不要**重新引入逐工具 API 手册（该层已刻意删除，由实时 Schema 取代）

## Token 失效（错误码 400006）

1. 访问上方授权页重新授权，取得新 token
2. 更新所用 MCP 客户端中 `tencent-docs` server 的 Authorization 配置
3. 若脚本按厂商约定经 `TENCENT_DOCS_TOKEN` 环境变量直连端点，同步更新该变量
4. 重启会话生效
