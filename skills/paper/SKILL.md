---
name: paper
description: 学术论文全流程：获取论文 PDF、HTML 与 TeX 源码，提取或整理可读文本，建立论文库，并按方法论文或综述论文分别阅读分析，形成可追溯、可续读的 report.md。适用于下载文献、论文转 Markdown/提取文本、整理文献库、读论文/精读/分析论文（analyze paper / read paper）、理解给定论文或批量处理文献，以及获取 CVPR、NeurIPS、ICML 等指定版本。arXiv 系优先获取 TeX 源码，默认提取不做结构重排；仅需摘要或翻译时不用。
user-invocable: true
argument-hint: <论文标题/文件/目录/URL>
---

# 论文（paper）

论文全流程库：下载获取、整理为结构化文本（Markdown 等）、精读分析，全部产物沉淀进同一个论文库，以一份库索引贯穿状态。

## 模式路由（先判断，再读子手册）

下载、提取/整理和分析是三个步骤，有三个对应手册

- 下载：`references/download.md`
- 提取/整理：`references/to-source.md`
- 阅读/精读/理解：先读 `references/analysis.md` 的公共流程，再按论文实际内容选择方法论文或综述论文子手册；只加载本次需要的分支。

需要结合用户的模糊指令，决定本次要做多少流程，必要时可以反问：

- "处理一下这批文献"：反问用户
- "下载并整理"：下载→提取（默认档）
- "提供了一个 PDF 文件地址"：在对应的位置执行提取（默认档）→阅读
- "帮我阅读"：下载→提取（默认档）→阅读

## 共享约定（各模式都遵守）

### 整体文件夹结构

库位置默认对应工作区，但是用户指定优先，库根目录一份 `index.md`，一行一篇，下载与解析两种状态在一张表里贯穿：

```markdown
| 标题     | 来源页 URL                |本地文件                                                    | 下载内容           | 整理状态 | 阅读状态 |
| -------- | ------------------------- | ----------------------------------------------------------- | ------------------ | -------- | -------- |
| CVPR2026_TrajRAG_Wang | <https://openaccess...html> | `CVPR2026_TrajRAG_Wang/` |  CVF PDF、arXiv HTML、arXiv TeX Source      | 未开始   | 定位阅读（已完成）  |
```

库级与篇级 `index.md` 均有模板可复制：`templates/index-library-template.md`、
`templates/index-paper-template.md`。报告公共模板为 `templates/report-template.md`；阅读时按分析手册插入对应论文类型的正文模板。

- 下载如果失败，下载内容应该为空。
- 状态一律用纯文字词，不用对勾、叉、旗帜类符号。
- 篇级详情（元信息、章节页码映射、待核对位置）放各论文文件夹内的 `index.md`，与库索引并存、职责不同。

### 每个论文对应的文件夹结构

- 每篇论文一个文件夹：`<会议/期刊><年份>_<短名>_<一作姓氏>`（如 `CVPR2026_TrajRAG_Wang`）；缺会议信息时用 `arXiv<年份>` 或 `<年份>_<短名>_<一作姓氏>`，以信息可得为准。
- 源文件以论文全名命名，空格用 `_` 替代（如 `TrajRAG_Retrieving_Geometric-Semantic_Experience_for_Zero-Shot_Object_Navigation.pdf`），放在论文文件夹内，忽略特殊符号（如 `:` 不能作为文件名）；同源其他格式跟随同一主名：`<论文全名>.html`、`<论文全名>-src.tar.gz`（TeX，提取阶段解压到 `tex-source/` 原样交付，不做转换）。
- 源文件（PDF、HTML、TeX tar）一律保留，只是重命名并整理位置，不覆盖不删除；唯一例外是 TeX tar 解压到 `tex-source/` 后删除 tar 包（`tex-source/` 自此即为源文件）。
- 每篇论文只维护一份 `report.md`，由提取报告和阅读报告共用；多个章节源文件不分别建立报告。各模式只维护自己的报告区域，保留其他模式产物及人工修订。分段阅读时增量记录覆盖范围、证据位置和待续读事项，不因报告文件存在就判定已通读。

最终每个论文对应的文件夹形如：

```bash
CVPR2026_TrajRAG_Wang/
├── TrajRAG_Retrieving_Geometric-Semantic_Experience_for_Zero-Shot_Object_Navigation.pdf
├── TrajRAG_Retrieving_Geometric-Semantic_Experience_for_Zero-Shot_Object_Navigation.html
├── index.md # 解释文件夹以及以下的文件
├── report.md # 提取报告与阅读报告共用，分区维护
└── tex-source # 或者 markdown-source 等
```

### 纪律

- 诚实记录：URL 必须实测或有据（下载成功、HEAD 200、搜索结果佐证），不编造；推断的链接标注"推断"。
- 完成情况如实标为已完成/部分完成（尚未开始则写未开始）。阅读另记定位阅读、专题阅读或全文精读及实际范围；“专题阅读（已完成）”不表示全文已读，不写“已核对完成”这类暗示全量校验的说法。
- 只处理授权范围内的论文和输出。

### 环境

一律 `uv run` / `uv add` / `uvx`，不找、不装系统 Python。
