# 豆包搜索 MCP Server（本地镜像）

火山引擎联网搜索 API 的 MCP 封装，提供网页与图片搜索能力，返回结构化 markdown、权威分级、rerank 评分等。

> **来源**：[volcengine/mcp-server](https://github.com/volcengine/mcp-server) 官方仓库，
> 仅同步 `server/mcp_server_askecho_search_infinity/` 这一个子目录，不拉整个 monorepo。

## 同步方式

从官方仓库只拉取搜索子目录（需要 [GitHub CLI](https://cli.github.com/)）：

```bash
# 首次：sparse checkout 单目录
cd mcp/
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/volcengine/mcp-server.git _tmp_search
cd _tmp_search
git sparse-checkout set server/mcp_server_askecho_search_infinity
cp -r server/mcp_server_askecho_search_infinity ../mcp_server_askecho_search_infinity
cd .. && rm -rf _tmp_search

# 后续更新：重新 sparse checkout 后覆盖即可
```

如果没有 `gh` / `git sparse-checkout`，也可以手动从 GitHub 网页下载该子目录的文件。

## 凭据配置

复制 `.env.example` 为 `.env`，填入对应密钥（二选一）：

```bash
cp .env.example .env
```

| 鉴权方式 | 环境变量 |
|---|---|
| API Key（推荐，简单） | `ASK_ECHO_SEARCH_INFINITY_API_KEY` |
| 火山引擎 AK/SK | `VOLCENGINE_ACCESS_KEY` + `VOLCENGINE_SECRET_KEY` |

API Key 申请：https://console.volcengine.com/search-infinity/api-key

## 安装与运行

```bash
cd mcp/mcp_server_askecho_search_infinity
uv sync                                    # 安装依赖
uv run mcp-server-askecho-search-infinity  # stdio 模式启动（默认）
uv run mcp-server-askecho-search-infinity -t sse            # SSE 模式
uv run mcp-server-askecho-search-infinity -t streamable-http # Streamable HTTP
```

## Tools

### `doubao_search`

联网搜索 API 调用，支持网页和图片搜索。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `Query` | string | 是 | 搜索 query，1~100 字符 |
| `Count` | int | 否 | 返回条数；web 最多 50，image 最多 5，默认 10 |
| `SearchType` | string | 否 | `web`（默认）或 `image` |
| `TimeRange` | string | 否 | `OneDay`/`OneWeek`/`OneMonth`/`OneYear` 或 `YYYY-MM-DD..YYYY-MM-DD` |
| `AuthLevel` | int | 否 | 权威等级过滤，0 默认，1 非常权威 |

## 定价

每月 500 次免费搜索，超出按量后付费或购买月卡套餐。

## License

[MIT](https://github.com/volcengine/mcp-server/blob/main/LICENSE) — volcengine/mcp-server
