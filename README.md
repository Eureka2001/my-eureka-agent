# My Eureka Agent

个人自建的 Agent Skills 与 MCP 源仓库。

## 内容结构

```text
my-eureka-agent/
├── AGENTS.md       # 仓库工作约定：工具链、MCP 契约、维护规范——先读这个
├── mcp.json        # 各客户端 MCP 条目分发模板（无凭据）
├── plugins.json    # 常用社区插件记录
├── skills/         # 自建 Skills
└── mcp/            # 自建 MCP server + eureka 网关（见 mcp/README.md）
```

## MCP

全部本地 MCP server 经 `eureka` 网关对外：客户端统一连
`http://127.0.0.1:1820/mcp`，后端按需启动、空闲回收、崩溃自愈。接入契约、
运维命令与架构约束见 `AGENTS.md`、`mcp/README.md` 与 `mcp/gateway/README.md`。

## 安全约束

凭据通过环境变量或各平台安全配置注入，不入库：API key、token、密码、
`.env`、平台运行时状态与日志缓存。`mcp.json` 为无凭据分发模板，可安全提交。
