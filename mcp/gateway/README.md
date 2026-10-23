# gateway/ —— eureka MCP 网关

把本地 6 个 MCP server 聚合为单入口 `eureka`：`tools/list` 由静态清单应答
（零后端 spawn），`tools/call` 按需拉起对应后端子进程并以 MCP client 代理，
结果（含 isError / structuredContent）原样透传；后端空闲超时自动回收，
崩溃自动重启。背景与设计决策见仓库 `.planning/2026-10-14-eureka-gateway/`。

## 运行

```bash
cd mcp/gateway
uv run server.py            # stdio（调试/直挂形态）
uv run server.py --http     # streamable-http @ 127.0.0.1:1820（前台）
```

### 后台常驻（pwsh，tmux 式 detach/attach）

```powershell
# 启动：隐藏窗口、与终端无关，任务管理器里是 pythonw.exe（路径含本目录）
Start-Process "D:\Repositories\my-eureka-agent\mcp\gateway\.venv\Scripts\pythonw.exe" `
  -ArgumentList "server.py","--http" `
  -WorkingDirectory "D:\Repositories\my-eureka-agent\mcp\gateway" -WindowStyle Hidden

# attach：跟随日志（Ctrl+C 只中断跟随，不杀服务）
Get-Content D:\Repositories\my-eureka-agent\mcp\gateway\logs\gateway.log -Wait -Tail 30

# kill：按端口定位（硬杀安全——活跃后端会经 stdin EOF 自行退出，已实测）
Stop-Process -Id (Get-NetTCPConnection -LocalPort 1820 -State Listen).OwningProcess
```

重复启动安全（单实例保护：探测到 1820 已监听则直接退出）。

### 开机自启（计划任务）

```powershell
powershell -ExecutionPolicy Bypass -File D:\Repositories\my-eureka-agent\mcp\gateway\install-task.ps1            # 安装（幂等）
powershell -ExecutionPolicy Bypass -File D:\Repositories\my-eureka-agent\mcp\gateway\install-task.ps1 -Status    # 状态
powershell -ExecutionPolicy Bypass -File D:\Repositories\my-eureka-agent\mcp\gateway\install-task.ps1 -Uninstall  # 卸载
```

登录即启动；每 10 分钟看门狗（已运行则跳过、进程死亡则下次触发自动复活）；
崩溃 1 分钟后自动重启；已禁用任务默认的 72h 运行时限。注意：本文件是带 BOM
的 UTF-8（PowerShell 5.1 无 BOM 会按 ANSI 误读中文注释）。

冒烟：`uv run scripts/smoke_http.py [--call qr_backends]`。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MCP_TRANSPORT` / `--http` | `stdio` | `http` / `streamable-http` 走 HTTP 模式 |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `1820` | HTTP 监听地址 |
| `GATEWAY_IDLE_TIMEOUT` | `180` | 后端空闲回收阈值（秒） |
| `GATEWAY_REAP_INTERVAL` | `15` | 回收巡检间隔（秒） |
| `GATEWAY_CALL_TIMEOUT` | `600` | 单次工具调用超时（秒），超时强制回收后端 |
| `GATEWAY_SPAWN_TIMEOUT` | `30` | 后端启动握手超时（秒） |
| `GATEWAY_COOLDOWN_BASE` | `5` | 异常早夭的指数退避基数（5→10→20…上限 60s） |
| `GATEWAY_LAUNCHER` | `venv` | `venv` 直连后端解释器（省 ~25MB/链）；`uv` 为开发模式 |
| `GATEWAY_LOG_FILE` | HTTP 模式默认 `logs/gateway.log` | 滚动日志路径；`0` 关闭文件日志 |

## tools.json 再生成

后端增改工具后：

```bash
uv run scripts/dump_manifest.py            # 全部 6 后端
uv run scripts/dump_manifest.py --only fetch,ocr
```

任一后端失败时清单只含成功部分且退出码为 1。habitica 凭据走
`HABITICA_*` 环境变量（用户级环境或仓库根 `.env`，网关代为注入子进程）。

## 架构约束（改代码前必读）

- **释放内存的唯一单位是子进程**：回收 = 关 stdin（EOF）→ 等退出 →
  `taskkill /T /F` 杀整棵树。Windows 下 venv python 是 trampoline，只杀
  直接子进程会留孤儿 base 解释器。
- **所有子进程必须带 `CREATE_NO_WINDOW`**（`_CREATION_FLAGS`）：网关跑在
  pythonw 下没有控制台，无标志地 spawn 控制台子进程（后端 exe、taskkill）
  时 Windows 会为其新建可见终端窗口——默认终端应用为 Windows Terminal 时
  用户桌面会真的弹出一个终端。
- **anyio cancel scope 只能由进入它的 task 退出**：每个后端由常驻
  `_supervisor` 任务独占进程/转发任务/ClientSession 生命周期，调用方只发
  停止信号；不要从调用任务里退出这些资源。
- **死亡记账由 retire 调用方裁决**（`count_death`）：崩溃/异常死亡计入
  冷却，空闲回收/调用超时/网关关停不计——避免把优雅回收误判为崩溃。
- **读后端 stderr 必须容错解码**（`errors="replace"`）：网关跑在计划任务
  环境下没有 `PYTHONUTF8`，后端子进程 stderr 默认是 GBK；严格 UTF-8 解码
  一旦遇到中文诊断输出就崩掉整个 supervisor 会话，进行中的调用会挂死到
  call timeout。后端侧也应在启动时把 stderr reconfigure 成 UTF-8。
- 网关自身零凭据；后端凭据链路不变（dotenv 后端从 `__file__` 向上找
  `.env`，habitica 由 `backends.env_for` 注入）。

## 测试

```bash
uv run pytest && uv run ruff check . && uv run mypy
```

假后端（`tests/fake_backend.py`）覆盖：懒 spawn、透传、isError、崩溃重启、
冷却、空闲回收（含 tasklist 验证进程树死亡）、并发串行、关停。
