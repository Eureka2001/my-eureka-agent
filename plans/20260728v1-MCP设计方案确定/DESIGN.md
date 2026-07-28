# MCP 设计方案 — 可行性评估与最终建议

> 输入：`TASK.md` 的 5 条设想 + 三路网络调研（见 `findings.md`）。
> 产出：对每条设想的裁决 + 推荐的落地方案。本文档不含实现代码（实现是下一个 task）。

---

## 一、总体结论：方案可行，但需修正两处关键假设

你的整体方向（在本仓库 `mcp/` 用 uv 隔离开发若干 Python MCP、源码进 git、凭据走环境变量）**完全成立**，也是社区主流推荐路径。但调研发现两个与你原描述冲突的事实，必须先校正：

| 你的设想 | 实际情况 | 影响 |
|---|---|---|
| 「通过 cc-switch 一次性注册所有 MCP 到 ChatGPT Work」 | ① **ChatGPT Work 不支持本地 stdio MCP**，只吃远程（SSE/Streamable HTTP）；② **cc-switch 的 MCP 同步只覆盖 5 个 CLI 客户端**（Claude Code/Codex/Gemini CLI/OpenCode/Hermes），覆盖不到 ChatGPT Work / Qoder / Claude Desktop。 | ChatGPT Work 想用 → server 必须能跑 HTTP；Qoder/ChatGPT Work 的注册要各自手工配置，cc-switch 帮不上。 |
| 「stdio 或 HTTP 实现」二选一 | FastMCP 下两者切换只需改 `transport` 参数（≈5 行），**可做成双模**：同一 server 既 stdio 又 HTTP。 | 不必二选一——**默认双模**，一鱼多吃。 |

---

## 二、对原方案 5 条设想的逐条裁决

### ✅ 1. 在本仓库 `mcp/` 下开发 —— 采纳
- 仓库已有 `skills/` 子目录模式可参照；新增平级 `mcp/` 自然。
- 安全约束已就位（README + `.gitignore` 屏蔽凭据），与「凭据走 env」天然契合。

### ⚠️ 2. 软链接到 `~/.mcp-servers` —— 建议改为「直接引用仓库绝对路径 / 目录联接」
- `~/.mcp-servers` **非社区约定**，无标准收益；Windows symlink 需管理员/开发者模式，且「路径含空格会破坏 MCP」。
- **推荐**：客户端配置直接写仓库内 server 的绝对路径；若想路径与仓库位置解耦，用 Windows **目录联接** `mklink /J` （无需管理员权限），不要用 symlink。

### ✅ 3. stdio 或 HTTP —— 采纳，并升级为**双模默认**
- FastMCP：`mcp.run(transport="stdio"|"streamable-http")`，通过 CLI 参数/env 选择。
- **stdio**：喂给 Claude Code / Codex / Qoder（这些支持本地 stdio）。
- **HTTP**：跑一个常驻本地进程（或 mcp-remote 桥接）喂给 ChatGPT Work。
- 铁律：**stdio 模式日志只写 stderr**，绝不写 stdout。

### ✅ 4. 每个工具用 uv 独立 Python 项目隔离 —— 采纳
- 「一 server 一 `pyproject.toml`」是官方 + 社区主流，依赖隔离、可锁版本、可 `uvx` 拉起。
- 依赖固定 `mcp>=1.27,<2`（避开 2.0 RC）。

### ⚠️ 5. cc-switch 一次性注册到 ChatGPT Work / Qoder / WorkBuddy —— **部分不成立**
- cc-switch 能做的：把你的 server 定义**批量写入 Claude Code / Codex / Gemini CLI / OpenCode / Hermes** 的本地配置（注意它偶发不生效，需核对）。
- cc-switch 做不到：注册到 ChatGPT Work、Qoder、Claude Desktop——这些**各自手工配置**。
  - Qoder：Settings → Connectors & MCP → 粘贴 JSON（格式与 Claude Code 兼容）。
  - ChatGPT Work：必须先把 server 跑成 HTTP 远程，再以 URL 形式添加。
- WorkBuddy：检索不到该名称的可验证产品/MCP 文档，**请确认准确名称**后再定。

---

## 三、推荐架构

### 目录结构
```
mcp/
├── README.md                  # 总览：各 server 用途、注册片段、env 变量清单
├── _shared/                   # （可选）共用工具：http 下载、图片→base64、env 读取
├── vision/                    # GLM-4.6V 视觉理解
│   ├── pyproject.toml         # mcp>=1.27,<2 ; zai-sdk
│   └── server.py
├── ocr/                       # OCR（RapidOCR 本地 + 阿里云 RecognizeGeneral 云）
│   ├── pyproject.toml
│   └── server.py
├── qrcode/                    # QR 解码（pyzbar → wechat-qrcode fallback）
│   ├── pyproject.toml
│   └── server.py
└── fetch/                     # 网页抓取分级 fallback（httpx → Playwright → 抽图走 OCR/VLM）
    ├── pyproject.toml
    └── server.py
```
- 切 4 个独立 server（而非一个胖 server）：每域工具数少（≤7），agent 选错率低；依赖隔离（Playwright 重，不该污染 OCR）。
- 每个 server 内部统一封装 `run(mode)`：`mode=stdio` 或 `mode=http`，由 `--transport` 参数 / `MCP_TRANSPORT` env 决定。

### 4 个 server 的能力设计

| server | 主能力 | Fallback | 依赖要点 | env 变量 |
|---|---|---|---|---|
| **vision** | GLM-4.6V（image URL/base64 + prompt） | flash 免费版兜底 | `zai-sdk` | `ZHIPU_API_KEY` |
| **ocr** | 阿里云 `RecognizeGeneral`（中文强、**便宜**、**适合 PDF 文字抽取**） | —（已决策只做云 API） | `alibabacloud_ocr_api20210707` | `ALIYUN_OCR_*` |
| **qrcode** | pyzbar（多码） | OpenCV WeChatQRCode（模糊/倾斜）→ GLM-4.6V | `pyzbar`(+ZBar.dll) / `opencv-contrib-python` + 4 模型文件 | （无，或复用 `ZHIPU_API_KEY`） |
| **fetch** | Playwright 渲染抓取（JS/懒加载），HTML→markdown | — | `playwright` / `html2text` | （无） |

### 🔑 三者并列，按场景分工（非 vision 吞噬 OCR/QR）
- **qrcode**：确定性解码，VLM 不可替代（会幻觉、不可复现）。
- **ocr**：**更便宜**，且是 **PDF 文字抽取**的正确工具——PDF 用 OCR 远比逐页丢给 Vision 合适（成本/速度/准确率都更优）。输入应支持 PDF。
- **vision (GLM-4.6V)**：用于真正的看图理解（海报/图表/场景图），不是另两者的上位替代。

agent 选择因此更清晰：解码→qrcode，PDF/文档文字→ocr，图像语义理解→vision。

### 凭据与跨设备
- **凭据**：全部走环境变量；仓库内 `.mcp.json`/文档只出现 `${ZHIPU_API_KEY}` 这类占位。README 已有约束，遵循即可。
- **本机（Windows）**：`.env` + direnv，或 Windows Credential Manager → 启动 server 时注入。
- **跨设备**：源码 + project 级 `.mcp.json` 进 git；Mac 公司机不放个人 key → 自然不启用 vision/ocr/fetch（与你的描述一致）。绝对路径跨平台冲突 → 各设备本地维护一份 client 配置（或用相对仓库根的启动脚本）。

### 注册路径（按客户端）
| 客户端 | transport | 注册方式 |
|---|---|---|
| Claude Code | stdio | cc-switch 批量写入 / `claude mcp add` / 仓库 `.mcp.json` |
| Codex / Gemini CLI / OpenCode | stdio | cc-switch 批量写入 |
| Qoder / QoderWork | stdio | 手工：Connectors & MCP → 粘贴 JSON |
| ChatGPT Work | **http**（必须远程） | 本地常驻 HTTP 进程 → 以 URL 添加 |

---

## 四、建议的实施顺序（下一个 task）
1. **vision** 先做（投入最小、覆盖最广、是其它工具的 fallback 依赖）——验证 FastMCP 双模 + env 凭据 + Windows 注册链路打通。
2. **fetch**（依赖最重，Playwright；但解锁微信海报场景）。
3. **ocr**（阿里云云 API 优先，RapidOCR 作 fallback）。
4. **qrcode**（最轻，pyzbar → wechat-qrcode）。
每做完一个：用 MCP Inspector 验证 → 写入对应 client 配置 → 在 agent 里实测一次。

---

## 五、待你确认的决策点
1. **ChatGPT Work 是否必须支持？** 若是 → 接受「多跑一个本地 HTTP 进程」的复杂度；若否（Claude Code/Qoder 够用）→ 只做 stdio，省事。
2. **WorkBuddy 的准确产品名**？需确认才能定它的注册方式。
3. **OCR 路线**：确认「阿里云云 API 为主 + 本地 RapidOCR 兜底」是否符合预期（而非纯云 / 纯本地）。
4. **4 server 独立** vs **合并**（如 vision 吞掉 ocr/qrcode 成一个「图像」server）：默认独立，但可合并以减少进程数。
