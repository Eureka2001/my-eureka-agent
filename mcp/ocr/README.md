# mcp-ocr

阿里云「统一识别」（`RecognizeAllText`）MCP server。**便宜、适合 PDF/文档文字抽取**（PDF 用 OCR 远优于逐页丢 Vision），阿里云官方推荐的新接口。

## 工具

| 工具 | 作用 |
|---|---|
| `recognize_text(image)` | 识别图片/PDF 中的文字，返回 markdown 文本。`image` 支持本地路径 / URL / data: URI / 裸 base64。 |
| `ocr_health()` | 校验凭据是否配置（不发请求）。 |

## 环境变量（凭据，绝不入库）

| 变量 | 必需 | 说明 |
|---|---|---|
| `ALIYUN_OCR_AK_ID` | 是 | 阿里云 AccessKey ID |
| `ALIYUN_OCR_AK_SECRET` | 是 | 阿里云 AccessKey Secret |
| `ALIYUN_OCR_ENDPOINT` | 否 | 默认 `ocr-api.cn-hangzhou.aliyuncs.com` |

开通：阿里云主账号登录 https://ocr.console.aliyun.com → 开通「**统一识别**」（注意：非「通用文字识别」，两者是不同产品，本 server 用前者）。

## 运行

```bash
cd mcp/ocr
# 注入凭据（PowerShell 用 $env:；bash 用 export）
uv run server.py            # stdio
uv run server.py --http     # streamable-http（默认 127.0.0.1:8001）
```
`MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT` 同 qrcode。

## 注册到客户端

### Claude Code（stdio）
```bash
claude mcp add ocr -- uv run --directory D:/Repositories/my-eureka-agent/mcp/ocr server.py
```
凭据通过 client 配置的 `env` 字段注入，例如仓库 `.mcp.json`：
```json
{
  "mcpServers": {
    "ocr": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "D:/Repositories/my-eureka-agent/mcp/ocr", "server.py"],
      "env": {
        "ALIYUN_OCR_AK_ID": "${ALIYUN_OCR_AK_ID}",
        "ALIYUN_OCR_AK_SECRET": "${ALIYUN_OCR_AK_SECRET}"
      }
    }
  }
}
```

### Qoder
同款 JSON 粘贴。ChatGPT Work 需先以 HTTP 模式常驻进程再以 URL 添加。

## 安全
凭据全部走环境变量，仓库零凭据（遵循仓库 README 约束）。
