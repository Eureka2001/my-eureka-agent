# mcp-vision

视觉理解 MCP server。**GLM-4.6V / Qwen-VL 双后端**，环境变量切换，统一走各家 OpenAI 兼容端点。

定位：真正的「看图理解」（海报/图表/场景图/UI 截图）。文档/PDF 文字抽取用 `eureka_ocr`，二维码用 `eureka_qrcode`。

## 工具

| 工具 | 作用 |
|---|---|
| `understand_image(image, prompt?, backend?)` | 多模态理解图片，返回文字。`image` 支持本地路径/URL/data URI/base64。 |
| `vision_health()` | 报告默认后端配置状态（不发请求）。 |

## 环境变量

| 变量 | 必需 | 说明 |
|---|---|---|
| `VISION_BACKEND` | 否 | `glm`（默认）或 `qwen` |
| **GLM** | | |
| `GLM_API_KEY` | 用 glm 时 | 智谱 API key |
| `GLM_VISION_MODEL` | 否 | 默认 `glm-4.6v`（免费版可设 `glm-4.6v-flash`） |
| `GLM_BASE_URL` | 否 | 默认 `https://open.bigmodel.cn/api/paas/v4` |
| **Qwen** | | |
| `DASHSCOPE_API_KEY`（或 `QWEN_API_KEY`） | 用 qwen 时 | 阿里 DashScope key（与 ocr 的阿里云 key 同账号体系） |
| `QWEN_VISION_MODEL` | 否 | 默认 `qwen-vl-max` |
| `DASHSCOPE_BASE_URL` | 否 | 默认 `https://dashscope.aliyuncs.com/compatible-mode/v1` |

调用时可传 `backend="glm"|"qwen"` 临时覆盖。

## 运行 / 注册

```bash
cd mcp/vision
uv run server.py            # stdio
uv run server.py --http     # streamable-http（默认 127.0.0.1:8002）
```

### Claude Code
```json
{
  "mcpServers": {
    "eureka_vision": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "D:/Repositories/my-eureka-agent/mcp/vision", "server.py"],
      "env": {
        "VISION_BACKEND": "glm",
        "GLM_API_KEY": "${GLM_API_KEY}",
        "DASHSCOPE_API_KEY": "${DASHSCOPE_API_KEY}"
      }
    }
  }
}
```
Qoder 粘贴同款 JSON；ChatGPT Work 需 HTTP 常驻进程。

## 安全
凭据全部走环境变量，仓库零凭据。
