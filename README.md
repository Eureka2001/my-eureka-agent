# agent-skills

跨设备、跨平台复用的 Agent Skills 源仓库。

## 目录结构

```text
agent-skills/
├── agent-created-skills.json
└── skills/
    ├── mobile-podcast-ai-interview-briefing/
    ├── ai-research-topic-recommender/
    ├── ai-technical-doc-generator/
    ├── ai-research-experiment-planner/
    └── agent-skills-cross-platform-sync/
```

## 当前迁移范围

本仓库当前迁移的是 WorkBuddy 中由本会话创建并登记在 `agent-created-skills.json` 的自建 Skills：

- `mobile-podcast-ai-interview-briefing`
- `ai-research-topic-recommender`
- `ai-technical-doc-generator`
- `ai-research-experiment-planner`
- `agent-skills-cross-platform-sync`

没有迁移 WorkBuddy 市场技能、连接器技能、缓存、数据库、账号配置或任何密钥文件。

## 推荐使用方式

把本仓库作为唯一事实源，然后将 `skills/<skill-name>` 复制或链接到各平台的原生 Skills 目录。

常见目标位置：

```text
WorkBuddy:   C:\Users\<用户名>\.workbuddy\skills\
Claude Code: C:\Users\<用户名>\.claude\skills\
Codex 新版:  C:\Users\<用户名>\.agents\skills\
Codex 旧版:  C:\Users\<用户名>\.codex\skills\
```

短期建议使用复制安装；长期多平台使用时，可用 Windows Junction 或 symlink 让各平台目录指向本仓库中的同一份 Skill 源目录。

## 安全约束

不要把以下内容放进本仓库：

- API key、token、cookie、密码、`.env` 文件
- WorkBuddy 的数据库或运行时状态
- 连接器配置、MCP 配置、账号登录态
- 日志、缓存、临时文件

Skill 文件应尽量保持可移植，凭据通过环境变量或各平台的安全配置单独注入。
