# mcp-qrcode

本地 QR/条形码解码 MCP server。**确定性、离线、零成本**，不调用 VLM（避免幻觉）。

## 工具

| 工具 | 作用 |
|---|---|
| `decode_qrcode(image)` | 解码图片中的 QR/条形码。`image` 支持本地路径 / http(s) URL / data: URI / 裸 base64。多个码每行一个返回。 |
| `qr_backends()` | 报告当前后端就绪状态，排查环境用。 |

## 解码后端（自动 fallback）

1. **pyzbar** —— 轻量、多码、多格式（QR/DataMatrix/EAN 等）。
2. **OpenCV WeChatQRCode** —— 工业级，对模糊/倾斜/反光鲁棒（仅当 pyzbar 无结果时启用）。

两个后端都是可选的：缺一个不影响另一个运行；都没就绪时工具会明确提示缺什么。

## 运行

```bash
cd mcp/qrcode
uv run server.py                 # 默认 stdio
uv run server.py --http          # streamable-http（默认 127.0.0.1:8000）
```

环境变量：`MCP_TRANSPORT`(stdio|http)、`MCP_HOST`、`MCP_PORT`、`QR_MODELS_DIR`（默认本目录 `models/`）。

## 后端依赖安装（Windows 注意）

- **pyzbar**：`pip` 装好 Python 包后，还需系统 libzbar。Windows 需 `ZBar.dll`（放到 PATH 或本目录）。缺失时 pyzbar 自动降级，不影响 wechat 后端。
- **wechat-qrcode**：把 4 个模型文件放入 `models/`（或 `QR_MODELS_DIR` 指向的目录）：
  `det.prototxt`、`det.caffemodel`、`sr.prototxt`、`sr.caffemodel`
  （来源：[WeChatQRCode 模型](https://github.com/opencv/opencv_3rdparty/branches/wechat_qrcode)）。模型文件不入库（见 `.gitignore`）。

## 注册到客户端

### Claude Code（stdio）
```bash
claude mcp add eureka_qrcode -- uv run --directory D:/Repositories/my-eureka-agent/mcp/qrcode server.py
```
或仓库根 `.mcp.json`（project scope，团队共享）：
```json
{
  "mcpServers": {
    "eureka_qrcode": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "D:/Repositories/my-eureka-agent/mcp/qrcode", "server.py"]
    }
  }
}
```

### Qoder / QoderWork（stdio）
Settings → Connectors & MCP → +Add → 粘贴上方同款 JSON（`mcpServers.eureka_qrcode`）。

### ChatGPT Work（仅远程 HTTP）
先常驻起 HTTP 进程，再以 URL 添加：
```bash
MCP_TRANSPORT=http uv run --directory D:/Repositories/my-eureka-agent/mcp/qrcode server.py
# 客户端里添加 http://127.0.0.1:8000/mcp
```

## 安全
本 server 无需任何凭据，符合仓库「凭据零入库」约束。
