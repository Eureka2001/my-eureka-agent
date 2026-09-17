# My Eureka Agent

个人自建的 Agent Skills and MCP 源仓库。

## 内容结构

```text
my-eureka-agent/
├── plugins.json            # 常用的社区 Skill 等插件记录
├── skills/                 # 我自建 Skills
└── mcp/                    # 我自建 MCP server
```

## 安全约束

Skill 文件不应内嵌凭据，凭据通过环境变量或各平台的安全配置单独注入。不要把以下内容放进本仓库：

- API key、token、cookie、密码、`.env` 文件
- 平台的数据库、运行时状态、日志、缓存、临时文件
- 连接器配置、MCP 配置、账号登录态
