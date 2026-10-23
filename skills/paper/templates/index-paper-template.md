# <文件夹名> 论文解析索引

> 复制本模板为论文文件夹内的 `index.md`。篇级索引只管这一篇论文的详情；
> 库根目录的库级 `index.md`（一行一篇的状态表）另见 `templates/index-library-template.md`。

## 论文元信息

| 项目 | 内容 |
| --- | --- |
| 标题 | |
| 作者 | |
| 单位 | |
| 年份 / 会议 | （如 2024，CVPR 2024 / arXiv 2506.12345） |
| 标识符 | （DOI / arXiv id / 无则写 —） |
| 项目主页 | （无则写 —） |
| 原文语言 | |

## 源文件信息

| 项目 | 内容 |
| --- | --- |
| 源文件 | [<论文全名>.pdf](<论文全名>.pdf)（与本 index.md 同文件夹；HTML / TeX 源码同主名时一并列出） |
| SHA-256 | |
| 总页数 | （无 PDF 时注明 —） |
| 下载日期 | |
| 来源渠道 | （如 CVF Open Access / arXiv / 作者主页，含来源页 URL） |
| 提取日期 | |
| 所用工具 | （如 extract-pdf split，2026-10-23；TeX 路径写解压工具） |

## 章节到输出文件映射（物理页码从 1 起）

| 原文章节 | 页码 | 输出文件 |
| --- | --- | --- |
| Abstract | 1 | [markdown-source/00-front-matter.md](markdown-source/00-front-matter.md) |
| 1. Introduction | 1–2 | [markdown-source/01-introduction.md](markdown-source/01-introduction.md) |
| ... | | |

（TeX 路径则映射主 tex 文件与章节结构；精细整理档映射到
intro-related-work / method / experiments / abstract-conclusion / references 等六文件。）

## 文件导航

- [markdown-source/](markdown-source/) — 按章节切分的文本源
- [report.md](report.md) — 提取报告与精读报告

## 处理状态

（两档：已完成 / 部完成。说明核对范围——抽查了哪些位置、有无逐页目检——不夸大。）

## 待核对事项

1. （位置 + PDF 页码 + 问题描述；无则写 —）
