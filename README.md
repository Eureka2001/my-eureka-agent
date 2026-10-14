# My Eureka Agent

个人自建的 Agent Skills and MCP 源仓库。

## 内容结构

```text
my-eureka-agent/
├── AGENTS.md                # 给 coding agent 的仓库工作约定
├── mcp.json                 # 各客户端 MCP 条目的分发模板（无凭据）
├── plugins.json             # 常用的社区 Skill 等插件记录
├── skills/                  # 我自建 Skills
├── mcp/                     # 我自建 MCP server + 网关（见 mcp/README.md）
│   └── gateway/             # eureka 网关：聚合全部 server 的单入口
└── .planning/               # 多步骤工作的规划记录（gitignored）
```

## MCP：网关架构

各 Agent 客户端（ZCode / Codex / Claude Code）统一连接一个本地常驻网关
`eureka` @ `http://127.0.0.1:1820/mcp`，由它聚合 `mcp/` 下全部 server：

- **懒加载**：`tools/list` 走静态清单（零进程）；某工具被调用才 spawn 对应
  后端，空闲 180s 自动回收，崩溃自动重启；
- **内存收益**：从"每客户端 × 每 server 一条解释器链"（实测峰值 ~2GB / 25
  条进程链）收敛为全局一个常驻网关（~70MB）+ 按需暂态进程；
- **运维入口**：后台启停 / 看日志 / 开机自启的一条命令都在
  `mcp/gateway/README.md`；架构设计与硬约束见同文件「架构约束」。

日常维护只需记得一件事：后端 server 增改工具后重跑
`cd mcp/gateway && uv run scripts/dump_manifest.py`。

## 安全约束

Skill 文件不应内嵌凭据，凭据通过环境变量或各平台的安全配置单独注入。不要把
以下内容放进本仓库：

- API key、token、cookie、密码、`.env` 文件
- 平台的数据库、运行时状态、日志、缓存、临时文件
- 带凭据的连接器/MCP 配置（仓库里的 `mcp.json` 是无凭据的分发模板，指向
  localhost 网关，可安全提交；各客户端本地配置中内联 token 的条目不属于
  本仓库管辖）
