# agent-skills

跨设备、跨平台复用的 Agent Skills 源仓库。

## 目录结构

```text
agent-skills/
├── agent-created-skills.json    # 自建 Skills 登记清单
├── installed-plugins.json       # 已安装插件的精简记录（供参考）
└── skills/
    ├── mobile-podcast-ai-interview-briefing/
    ├── ai-research-topic-recommender/
    ├── ai-technical-doc-generator/
    ├── ai-research-experiment-planner/
    ├── agent-skills-cross-platform-sync/
    ├── trace-codechain/
    ├── zh2en/
    ├── english-checking/
    └── read-paper/
```

## 自建 Skills

`skills/` 目录下存放的是用户自建的 Skills，每个子目录是一个独立的 Skill，包含 `SKILL.md` 等文件。

已登记的自建 Skills 记录在 `agent-created-skills.json` 中。本仓库不包含任何平台的连接器配置、MCP 配置、缓存、数据库、账号配置或密钥文件。

## 安装到各平台

把本仓库作为唯一事实源，将 `skills/` 目录整体复制或链接到各平台的原生 Skills 目录。

常见目标位置：

```text
WorkBuddy:   C:\Users\<用户名>\.workbuddy\skills\
Claude Code: C:\Users\<用户名>\.claude\skills\
Codex 新版:  C:\Users\<用户名>\.agents\skills\
Codex 旧版:  C:\Users\<用户名>\.codex\skills\
```

短期建议使用复制安装；长期多平台使用时，可用 Windows Junction 或 symlink 让各平台目录指向本仓库中的同一份 Skill 源目录。例如 Claude Code 的 symlink：

```bash
# Claude Code（默认路径示例）
mklink /J "%USERPROFILE%\.claude\skills" "D:\Repositories\agent-skills\skills"

# Claude Code（别名路径示例）
mklink /J "%USERPROFILE%\.claude-zai\skills" "D:\Repositories\agent-skills\skills"
```

## 插件管理的 Skills

部分平台支持插件系统，可以安装第三方 Skills。这些 Skills 不在 `skills/` 目录中，由插件运行时动态加载，通常以 `<plugin-name>:<skill-name>` 形式调用（例如 `planning-with-files:plan`、`document-skills:pdf`）。

### 复现安装

以 Claude Code 为例：

**1. 添加第三方市场源**（内置市场无需手动添加）：

```text
/plugin marketplace add OthmanAdi/planning-with-files
/plugin marketplace add anthropics/skills
```

**2. 安装具体插件**：

```text
/plugin install planning-with-files@planning-with-files
/plugin install document-skills@anthropic-agent-skills
/plugin install skill-creator@claude-plugins-official
```

### 插件数据结构（Claude Code 参考）

插件状态分布在 Claude Code 配置目录下（注意别名情况）：

```text
~/.claude/  (或 ~/.claude-zai/)
├── settings.json                          # enabledPlugins + extraKnownMarketplaces
├── plugins/
│   ├── known_marketplaces.json             # 所有已知市场源（含内置）
│   ├── installed_plugins.json              # 已安装插件及版本/git SHA
│   ├── marketplaces/                       # 市场仓库的本地克隆
│   └── cache/                              # 插件安装缓存
└── skills -> /path/to/agent-skills/skills/ # 自建 Skills 的 symlink
```

本仓库中的 `installed-plugins.json` 是上述状态的精简记录，方便查阅当前环境装了哪些插件。其他平台如有类似的插件机制，可参照此记录手动复现。

## 安全约束

不要把以下内容放进本仓库：

- API key、token、cookie、密码、`.env` 文件
- 平台的数据库、运行时状态、日志、缓存、临时文件
- 连接器配置、MCP 配置、账号登录态

Skill 文件应尽量保持可移植，凭据通过环境变量或各平台的安全配置单独注入。
