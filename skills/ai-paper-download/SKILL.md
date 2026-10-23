---
name: ai-paper-download
description: 批量或单个下载学术论文的官方版 PDF，并生成记录官网 URL 与 PDF URL 的清单文件。只要用户提到"下载论文 / 论文 PDF / 文献下载 / 把参考文献的 PDF 下载下来 / 记录论文链接"，或要求 CVPR、ICCV、ECCV、NeurIPS、ICML、ACM、IEEE 等官方版本（而非 arXiv 版）时使用。核心策略：优先会议/期刊官方开放存档；付费墙论文默认停留在"记录 URL"一步，除非用户明确要求尽一切努力。
---

# AI 论文下载

为论文列表下载**官方渠道**的文件（Html、PDF、TeX 源码）并产出链接清单。

## 总策略（先读这个）

1. **按渠道分流，不同情况不同策略**：

   | 情况 | 策略 |
   |---|---|
   | CVPR / ICCV（CVF Open Access）、ECCV（ECVA）、NeurIPS（proceedings.neurips.cc）、ICML（PMLR）等开放存档 | **一定下载官方版**，不要偷懒用 arXiv 交差 |
   | IEEE 期刊（TIP/TPAMI 等）、ACM DL（MM 等）付费墙 | **停在 URL 一步**：记录官方落地页（IEEE Xplore / CSDL / ACM DOI 页），不再反复尝试 |
   | 付费墙但作者方公开挂了 PDF（实验室官网、作者主页，如 vipl.ict.ac.cn） | 算官方版，直接下载，并记录来源 URL |
   | 开放存档尚未收录（如 ICML 当年卷未上 PMLR） | 记录 OpenReview / 会议官网 URL，注明"官方卷未上线" |

2. **默认止损**：不好找的就停在"记录 URL"。只有用户明确说"尽一切努力 / 想办法搞到 PDF"时，才升级去试别的渠道（arXiv 备用版、作者主页、OpenReview 变通访问等）。升级时 arXiv 版文件名加 `-arXiv` 后缀以示区分。
3. **诚实记录**：不编造 DOI 和 URL。每个写入清单的 URL 要么实际下载成功，要么 HEAD 200，要么有搜索结果佐证；推断出的链接要标注"推断"。
4. 识别非论文条目（竞赛获奖、数据集、软件）并跳过；参考文献里的重复条目先去重（常见如 [7]=[23]、[11]=[19] 同文两编号）。

## 工作流程

### 1. 提取论文清单

- docx 提正文和参考文献：`pandoc -f docx -t plain 文件.docx -o out.txt`（python-docx 为备用）。
- 从参考文献编号 [N] 建立任务表：编号 | 标题 | 出处 | 作者。正文中出现但参考文献缺标题的（如"TrajRAG"），回正文找全标题。
- 顺带把编号和短名定为输出文件名：`[NN] 短名-VENUE年.pdf`，例如 `[01] HOZ-ICCV2021.pdf`。全批次统一，便于追溯。

### 2. 并行派发（清单 ≥ 5 篇时）

- 用 general-purpose subagent，**每批 5–6 篇**。提示词必须自包含：环境（Windows/Git Bash）、输出目录、每篇的精确文件名、下载与验证命令、来源优先级、"最后一条消息必须给结构化报告（编号|标题|官方页URL|PDF直链|本地文件|大小|状态）"、"URL 必须实际验证，不得编造"。
- 明确禁止 subagent 用浏览器自动化，只用 WebSearch/WebFetch/curl。
- **subagent 可能被中途取消**：失败/取消后先 `ls` 磁盘看已落地的文件再决定重派范围，别全量重跑；被取消的 agent 可能已完成一半但没留 URL——文件有效就保留，URL 可事后自己补查（搜 `标题 + 官网域名`）。

### 3. 定位官方 URL（渠道速查）

| 渠道 | 定位方法 | URL 模式 / 坑 |
|---|---|---|
| CVF Open Access（CVPR/ICCV） | WebSearch `openaccess.thecvf.com 标题`，或按 slug 规则构造后 `curl -sI` 验证 | abstract 页 `/content/CVPR2024/html/Slug_CVPR_2024_paper.html`；PDF 同路径 `/papers/`。**slug 以官网实际拼写为准**（官网可能有拼写错误，见坑 3） |
| ECVA（ECCV） | WebSearch `ecva.net 标题` | 先拿到 `.../html/1315_ECCV_2022_paper.php`，**PDF 文件名与页面编号不同**（实际是 `.../papers/136990295.pdf`），必须从 php 页里提取真实链接 |
| NeurIPS | WebSearch `proceedings.neurips.cc 标题` | `/paper_files/paper/YYYY/hash/<hash>-Abstract-Conference.html` → PDF 把 `hash/...-Abstract` 换成 `file/<hash>-Paper-Conference.pdf` |
| ICML / PMLR | 查 `https://proceedings.mlr.press/` 主页卷列表 | **卷会滞后**：当年 7 月开的会，9 月可能还没上线（ICML 2025 = v267）。未上线 → 记录 OpenReview 论坛页 + icml.cc 虚拟页，注明待 PMLR |
| IEEE（TIP/TPAMI） | WebSearch 标题 + ieeexplore | 只记录：Xplore `https://ieeexplore.ieee.org/document/<id>/`、CSDL `computer.org/csdl/...`、DOI（文档给了就直接记）。Xplore 对 curl 返回 202/403 反爬，属正常，不代表链接失效 |
| ACM（MM 等） | WebSearch 标题 + dl.acm.org | 只记录 DOI 页（如 `https://dl.acm.org/doi/10.1145/3581783.3612351`）。部分作者方（实验室官网）会挂正式版 PDF，可搜 `标题 + pdf` 找到 |
| arXiv（备用/判别） | 仅在策略允许升级时用 | arXiv PDF 有水印标记，本地验证：`grep -a -o "arXiv:[0-9v.]*" 文件` |

### 4. 下载与验证（每个文件必做）

```bash
curl -sL -A "Mozilla/5.0" -o "[01] HOZ-ICCV2021.pdf" "<PDF直链>"
head -c 5 "[01] HOZ-ICCV2021.pdf"   # 必须输出 %PDF-
ls -la                               # 必须 > 100KB
curl -sI -A "Mozilla/5.0" "<PDF直链>" | grep -i content-length   # 与本地字节数对账，确认来源
```

- **绝不能把 HTML 存成 .pdf**：OpenReview/ACM/IEEE 被拦截时返回的 HTML 报错页大小只有 ~12KB，`<title>Error 403 | OpenReview</title>` 一查便知。发现就删除该文件，改记 URL。
- 下载源 URL 必须留痕：subagent 报告里要有，否则事后无法写入清单。

### 5. 产出清单文件

写一个 `论文链接清单.md`，含统计头（共几篇、下载几篇、仅记 URL 几篇及原因）+ 两张表。示例行：

```markdown
| [10] | Imagine Before Go: Self-Supervised Generative Map for Object Goal Navigation | CVPR 2024 | https://openaccess.thecvf.com/content/CVPR2024/html/Zhang_Imagine_Before_Go_...html | https://openaccess.thecvf.com/content/CVPR2024/papers/Zhang_Imagine_Before_Go_...pdf | `[10] ImagineBeforeGo-CVPR2024.pdf` |
```

仅记 URL 的表：编号 | 标题 | 出处 | 官方页面 URL（多渠道并列）| 未下载原因。CVF 有补充材料的（`/supplemental/` 路径）把链接一并附上。

### 6. 汇报

先说结果（几篇成功、几篇只记 URL、各自原因），再列产出文件路径。

## 踩坑记录（防再踩）

1. **OpenReview 全面反爬**：对 curl 一律 403（含 `/pdf?id=` 和 hash 型 PDF 直链，加浏览器头也没用）。别恋战，记录 URL 即可，浏览器中人工可开。
2. **PMLR 卷滞后**：不要假设当年 ICML 已在 proceedings.mlr.press，先抓主页卷列表确认。
3. **CVF slug 拼写错误**：官网把 "Rearrangement" 拼成 "Rearrangment"，按正确拼写构造的 URL 会 404。构造失败就 WebSearch 或抓 abstract 页拿真实链接，别反复改拼写重试。
4. **ECVA 页面编号 ≠ PDF 文件名**（见速查表）。
5. **ACM/IEEE DOI 页 curl 返回 HTML 登录/校验页**，大小仅几 KB~几十 KB——未验证文件头就保存是最常见的假成功。
6. **重复引用**：申报书类文档常有同文两编号，去重后再分派，否则重复下载。
7. **Windows/Git Bash 细节**：中文路径和文件名没问题（cd 过去再操作更稳）；`/tmp` 可用；curl 记得 `-A "Mozilla/5.0"`；DNS 失败（exit 6）就换域名变体（有无 www）；本机 grep 是 ugrep，复杂 `{0,120}` 量词正则会报错，用简单模式或 python。
8. **别用 arXiv 交差**：开放存档渠道（CVF/ECVA/NeurIPS/PMLR）都可达且 curl 友好，arXiv 只作为用户明确要求后的备用，且要加 `-arXiv` 后缀标注。
