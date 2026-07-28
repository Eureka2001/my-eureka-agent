# 任务计划：MCP 设计方案确定

> 目标：综合评估「在本仓库 `mcp/` 下开发 4 个本地 MCP 工具 + 软链接 + cc-switch 注册」方案的可行性，结合网络最佳实践，给出可落地的最终设计方案（不是开始写代码）。

## 目标声明

在 `D:\Repositories\my-eureka-agent\mcp\` 开发以下 4 个 MCP 工具，作为各 Agent 客户端的本地能力兜底：

1. **视觉理解** — 调用 GLM-4.6V（智谱）等 VLM API
2. **OCR（中文为主）** — 调用阿里云 OCR API（备选本地 PaddleOCR/RapidOCR）
3. **QR Code 识别** — 本地解码（pyzbar / wechat-qrcode 等）
4. **稳定网页抓取** — 至少支持延迟加载（JS 渲染）

## 关键约束（来自 TASK.md / README）

- 凭据 **绝不入库**（README 安全约束已写明）；通过环境变量或各平台安全配置注入。
- 视觉/OCR 不用本地模型，用云 API（GLM-4.6V / 阿里云 OCR）—— 因本地中文能力不足。
- 每个工具用 **uv 管理的独立 Python 项目**，彼此隔离。
- 主要目标设备：当前 Windows 11 笔记本（无 NVIDIA GPU）。Mac 仅Coding 用途，暂不重点考虑。
- 通过 cc-switch + 仓库同步实现跨设备迁移（公司 Mac 不放个人 API Key）。

## 阶段

### 阶段 1：现状盘点 ✅ complete
- 读取仓库结构、README 安全约束、TASK.md。
- 确认 `mcp/` 当前为空，仓库已有 `skills/` 子目录模式可参照。

### 阶段 2：网络最佳实践调研 ✅ complete
- 路线 A：MCP Python SDK + uv + stdio/HTTP 取舍 ✅
- 路线 B：cc-switch 能力边界 + 各客户端注册方式 ✅
- 路线 C：网页抓取/OCR/QR/视觉 现成方案对比 ✅

### 阶段 3：可行性评估与方案裁决 ✅ complete
- 对 TASK.md 中的 5 条设想逐条裁决（见 DESIGN.md 第二节）。
- 产出最终架构决策：目录结构、transport 选型、依赖隔离、注册路径。

### 阶段 4：交付设计文档 ✅ complete
- 已写 `findings.md`（三路调研结论）+ `DESIGN.md`（评估与最终方案）。
- 未写实现代码（实现是下一个 task）。

### 阶段 5：等待用户确认 4 个决策点 ⏳ in_progress
- ChatGPT Work 是否必须支持（决定是否上 HTTP 层）。
- WorkBuddy 准确产品名。
- OCR 路线确认。
- server 粒度（4 独立 vs 合并）。

## 遇到的错误
| 错误 | 尝试次数 | 解决方案 |
|------|---------|---------|
| （暂无） | | |

## 用户已确认的决策（2026-07-28）
- **ChatGPT Work**：代码做双模（stdio + HTTP），但当前只实测 stdio；HTTP 留到真要用时再测。
- **OCR 路线**：只做云 API（阿里云 RecognizeGeneral），不做本地 RapidOCR。
- **server 粒度**：4 个独立 server。
- **首个实现**：qrcode（打通 FastMCP 双模 + env + Windows 注册链路）。

## 决策日志
- **transport**：双模默认（stdio + streamable-http），FastMCP 下成本极低；避免「stdio 或 HTTP 二选一」。
- **server 粒度**：默认 4 个独立 server（vision/ocr/qrcode/fetch），每域 ≤7 工具；待用户确认是否合并。
- **软链接**：否决 `~/.mcp-servers` symlink；改用直接绝对路径或 Windows 目录联接 `mklink /J`。
- **cc-switch 定位**：仅用于批量注册到 5 个 CLI；ChatGPT Work/Qoder 需各自手工配。
- **ChatGPT Work**：本地 stdio 不支持 → 若必须支持则跑 HTTP 进程；待用户确认。
- **OCR/QR 取向（用户修订）**：三者并列、按场景分工，**vision 不作主轴**。QR 需确定性解码（VLM 不可替代）；OCR 更便宜且是 PDF 文字抽取的正确工具（PDF 用 OCR 远优于 Vision）；vision 用于真正的看图理解。
- **路径方案**：用户确认采用 `mklink /J`（目录联接，Windows 无需管理员）。
- **凭据**：全部 env 注入，仓库零凭据（遵循 README 约束）。
