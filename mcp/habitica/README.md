# eureka_habitica

使用 [官方 Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk) 内置的 **FastMCP**，通过 [Habitica 官方 API](https://apidoc.habitica.com/) 连接与网页相同的账户、任务和标签数据。

仅支持 **STDIO**：由 MCP 客户端启动进程，不需要提前启动服务。沿用本仓库 SDK 1.x 的依赖约定（`mcp>=1.27,<2`），具体版本由 `uv.lock` 固定；HTTP 请求使用异步 HTTPX，参数使用 Pydantic 校验。

## 准备凭据

在 Habitica 网页的 [设置 → API](https://habitica.com/user/settings/api) 查看 User ID 和 API Token，将本目录的 `.env.example` 复制为 `.env` 并填写：

| 环境变量 | 含义 |
| --- | --- |
| `HABITICA_USER_ID` | 要连接的账户 User ID |
| `HABITICA_API_TOKEN` | 对应账户 API Token |

只需配置上述两个变量。服务会自动生成 `HABITICA_USER_ID-eureka-habitica` 作为每次请求的 `X-Client` header。

`HABITICA_CLIENT_ID` 是可选覆盖项，省略或留空都会使用自动生成的值。若将服务提供给别人，可覆盖为 `工具维护者的UserID-eureka-habitica`。格式要求来自 [Habitica 官方调用规范](https://github.com/HabitRPG/habitica/wiki/API-Usage-Guidelines)。

凭据也可以由 MCP 客户端通过环境变量注入。服务不会自行寻找或读取 `.env`；文件方式通过 `uv --env-file` 明确加载。真实 `.env` 已被忽略，不应提交。

## 运行

首次安装：

```powershell
Set-Location D:\Repositories\my-eureka-agent\mcp\habitica
uv sync --locked --no-dev
```

在 MCP 客户端的连接设置里使用以下启动命令和参数，由客户端负责启动：

```text
command: uv
args:
  run
  --locked
  --no-dev
  --directory
  D:/Repositories/my-eureka-agent/mcp/habitica
  --env-file
  D:/Repositories/my-eureka-agent/mcp/habitica/.env
  server.py
```

如果客户端直接注入上述两个环境变量，省略 `--env-file` 及紧随其后的路径即可。按实际位置调整绝对路径；这个命令可以从任意工作目录运行。

手动检查启动时，可以运行：

```powershell
uv run --locked --no-dev --env-file .env server.py
```

它将等待 STDIO 的 MCP 消息。推荐在 MCP 客户端先调用 `habitica_health` 验证认证，再调用 `list_tasks` 查看任务。缺少或无效配置会在启动时向 stderr 给出提示。

## 工具

| 工具 | 用途 |
| --- | --- |
| `habitica_health` | 一次账户查询检查认证和连接 |
| `get_user` | 名称、等级、生命值、经验、金币和日重置设置 |
| `list_tasks` | 列出习惯、每日任务、待办、奖励或已完成待办 |
| `get_task` | 按任务 UUID 或别名读取详情 |
| `create_task` | 创建任务，可包含清单、标签、难度和重复规则 |
| `update_task` | 局部修改指定字段 |
| `delete_task` | 删除任务 |
| `score_task` | 正负向习惯打卡、完成/取消每日任务或待办、兑换自定义奖励 |
| `add_checklist_item` | 添加 daily/todo 清单项 |
| `update_checklist_item` | 明确设置清单项文字和完成状态 |
| `delete_checklist_item` | 删除清单项 |
| `list_tags` | 读取标签 UUID 和名称 |
| `create_tag` | 创建标签 |
| `update_tag` | 重命名标签 |
| `delete_tag` | 删除标签并从关联任务移除 |

`list_tasks.task_type` 支持 `habits`、`dailys`、`todos`、`rewards`、`completedTodos`；默认不包含已完成待办。`completedTodos` 由 Habitica 限定为最近 30 个。任务详情和清单返回完整结构化数据，便于随后使用 UUID 操作。

创建待办的 MCP 参数示例：

```json
{
  "task": {
    "type": "todo",
    "text": "读完本周文章",
    "notes": "记录三个要点",
    "priority": 1.5,
    "date": "2026-10-12",
    "checklist": [{"text": "阅读"}, {"text": "整理笔记"}]
  }
}
```

创建每日任务时可指定 `frequency`、`everyX`、`repeat`、`startDate`、`daysOfMonth` 和 `weeksOfMonth`。`repeat` 的星期键为 `su/m/t/w/th/f/s`；使用频率和重复规则须遵循 Habitica 的含义。难度 `priority` 为 `0.1/1/1.5/2`（琐碎/简单/中等/困难）。奖励的 `value` 为消耗的金币。

更新操作只发送指定字段。`notes=""` 清空备注，`tags=[]` 清空标签，`date=null` 清空截止日期；省略字段不会覆盖它。清单项更新要求同时提供 `text` 和 `completed`，请先读取并保留不想修改的值。

## 调用行为

- 默认所有 API 请求串行且至少间隔 **30 秒**，符合 Habitica 对后台自动脚本的规范；连续调用可能等待，请将客户端工具超时设为至少 60 秒，并依次调用。
- 可选 `HABITICA_REQUEST_INTERVAL_SECONDS` 只能增加间隔；`HABITICA_TIMEOUT_SECONDS` 控制单次 API 网络超时，默认 20 秒。多个服务进程各自计时，不应同时对同一账户运行后台自动调用。
- 429 响应遵循 `Retry-After` 并进入冷却；限流预算用完时按 `X-RateLimit-Reset` 冷却。冷却期间调用返回可理解的错误，不发送更多请求。
- 所有请求只执行一次，不自动重试。写操作超时或连接中断后，先查询状态；重复创建会新增任务，重复习惯打卡会再次改变账户数值。
- `score_task` 的 `up` 表示正向习惯、完成 daily/todo 或兑换 reward；`down` 表示负向习惯或取消 daily/todo 完成。兑换 reward 会扣金币。
- 读取、修改、删除和打卡工具带有 MCP 行为注解；注解是客户端提示，不替代用户授权。
- 账户读取只选择必要字段；返回数据和错误会去除认证字段并遮盖 API Token。诊断信息使用框架的 stderr 日志；stdout 专用于 MCP 协议。
- 群组和挑战任务仍受 Habitica 的权限限制；当前服务专注个人任务，不提供群组、付费商品或账户重置操作。

## 开发验证

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format . --check
uv run mypy
uv run pytest -q -p no:cacheprovider
```

测试使用模拟 Habitica API 和官方 SDK 的真实 MCP 会话，覆盖 15 个工具的路由、类型校验、认证头、凭据遮盖、错误、串行请求、冷却和无自动重试，并通过子进程验证 STDIO 握手及工具发现。测试不访问真实账户，也不产生真实任务变更；真实认证请配置凭据后调用 `habitica_health`。
