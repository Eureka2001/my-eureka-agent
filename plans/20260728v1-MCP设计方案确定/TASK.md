我本地使用 ChatGPT Work, WorkBuddy 和 QoderWork 等许多 Agent 工具，同时自己也有大量的 MCP 需求，目前最突出的需求是

1. 视觉理解
2. OCR，主要是中文
3. QR Code 识别
4. 极其稳定可靠的网页获取（至少包含延迟加载能力）。

这些需求，有一些被各个 Agent APP 实现了。比如 WorkBuddy、QoderWork 有自带的网页获取能力、ChatGPTWork 有自带的浏览器能力和 Chrome 浏览器控制能力。而在选择使用多模态大语言模型时，一些框架也会提供视觉理解能力。但是有的大家都没有，比如 OR Code 解码能力。

国内的工具（WorkBuddy 和 QoderWork ）还是挺追求大而全的，都会有基础的网页抓取能力。但是比如一个微信链接，其中用海报替代了正文，正文一个字符都没有，只有几个 PNG 文件，这时就需要模型（特别是非多模态的模型）可以调用 OCR 或者进行视觉理解。

我的目标是，在本仓库开发几个 MCP 工具，后面我接入到各个 Agent 中作为本地工具兜底。我计划开发这些 MCP 在 `mcp/` 文件夹中。特别的，视觉理解能力、OCR 工具我不打算使用本地的模型进行，一般而言这些模型的能力达不到预期，特别是中文场景。我打算使用 GLM 4.6V、阿里云的 OCR API 这种工具，我可以采购 API KEY 进行调用。

这种情况下，我有如下考虑：

1. 将当前仓库 `D:\Repositories\my-eureka-agent` 下开发我所需要的 MCP
2. 在我的主目录下 `~/.mcp-servers` 通过文件夹软链接到当前的 mcp server
3. 通过 stdio 的 MCP Server 或者 HTTP 的 MCP 进行实现。 
4. 每个工具以 UV 管理的 python 进行实现，UV 之间彼此隔离，避免相互污染。
5. 通过 cc-switch 一次性注册我的所有 MCP 到 ChatGPT Work，而 Qoder 和 Workbuddy 也可以进行导入操作。

我需要你综合评估这个方案的可行性，并上网检索类似需求的最佳实践，给我建议。

关于跨设备迁移，我通过 cc-switch 进行管理我的订阅，因为我的 ChatGPT Work 其实用的是 GLM 5.2。使用 cc-switch + 本仓库同步的方式，实现 MCP 的跨设备迁移。但我其实只有一台个人 Windows 电脑（无 Nvidia GPU 的笔记本），一台公司电脑（Mac M5 Air）。暂时多设备同步的需求，其实也不高，因为我不会在公司电脑放我的 API Key，而且公司电脑主要处理 Coding，不需要上述的浏览器、视觉能力。所以我们先专注于在本设备中进行实现。
