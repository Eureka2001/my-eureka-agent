# 论文下载

为论文清单拿到文件（PDF 为默认交付物，HTML 与 TeX 源码按需），并把结果落成论文文件夹与库索引。库位置、文件夹命名、索引结构见 SKILL.md 共享约定。

## 策略基调

目标是把论文拿到手，如实记录来源即可。实操按"命中率高、curl 友好"排序尝试：

1. **开放存档首选**：CVF（CVPR/ICCV）、ECVA（ECCV）、NeurIPS proceedings、PMLR（ICML）对 curl 友好，通常一步到位。
2. **arXiv 几乎同等正式**：直接用，文件名与索引里不做特殊标注，来源如实标注 arXiv。**arXiv 系论文首先下载 TeX 源码**（`arxiv.org/e-print/<id>`）作为来源——它既是最好的文本源，也顺带确认了论文的可提取性；PDF（`arxiv.org/pdf/<id>`）与 HTML（`arxiv.org/html/<id>`，旧论文用 ar5iv）作为补充按需再取。
3. **止损默认**：付费墙（IEEE Xplore、ACM DL）与全面反爬（OpenReview）不硬刚，停在记录来源页 URL 并注明原因；用户明确说"尽一切努力 / 想办法搞到 PDF"才升级尝试其他途径。
4. 作者方公开挂出的 PDF（实验室官网、作者主页，如 vipl.ict.ac.cn）与会议官方版同等可用，下载并记录来源 URL。
5. 开放存档尚未收录（如 ICML 当年卷未上 PMLR）：记录 OpenReview / 会议官网 URL，注明"官方卷未上线"。

每个写入索引的 URL 都要有据：实际下载成功、HEAD 200、或有搜索结果佐证；推断出的链接标注"推断"。

## 工作流程

### 1. 整理论文清单

- 常见输入是标题、URL 或直接给出的论文清单，逐一登记即可。
- 仅当用户给的是 docx/pdf 等文档（如从申报书里批量下参考文献）才需要先提取清单：`pandoc -f docx -t plain 文件.docx -o out.txt`（python-docx 为备用），从参考文献编号 [N] 建任务表：编号 | 标题 | 出处 | 作者。正文中出现但参考文献缺标题的（如"TrajRAG"），回正文找全标题。
- 识别非论文条目（竞赛获奖、数据集、软件）并跳过；重复引用去重（常见如 [7]=[23]、[11]=[19] 同文两编号），编号沿用首次出现。
- 顺带确定每篇的文件夹名 `<会议><年份>_<短名>_<一作姓氏>`（如 `ICCV2021_HOZ_Zhang`），全批次统一，便于追溯。一作姓氏：外文作者用原姓（Smith），中文作者用拼音姓（Zhang、Wang、Li）；不取名的首字母缩写。

### 2. 并行派发（清单 ≥ 5 篇时）

- 用 general-purpose subagent，**每批 5–6 篇**。提示词必须自包含：环境（Windows/Git Bash）、库目录、每篇的精确文件夹名、下载与验证命令、渠道尝试顺序、"最后一条消息必须给结构化报告（标题|来源页URL|本地文件|下载内容|大小）"、"URL 必须实际验证，不得编造"。
- 明确禁止 subagent 用浏览器自动化，只用 WebSearch/WebFetch/curl。
- **subagent 可能被中途取消**：失败/取消后先 `ls` 库目录看已落地的文件夹再决定重派范围，别全量重跑；被取消的 agent 可能已完成一半但没留 URL——文件有效就保留，来源页 URL 可事后补查（搜 `标题 + 渠道域名`）再补进索引。

### 3. 定位下载源（渠道速查）

| 渠道 | 定位方法 | URL 模式 / 坑 |
|---|---|---|
| CVF Open Access（CVPR/ICCV） | WebSearch `openaccess.thecvf.com 标题`，或按 slug 规则构造后 `curl -sI` 验证 | abstract 页 `/content/CVPR2024/html/Slug_CVPR_2024_paper.html`；PDF 同路径换 `/papers/`。slug 以官网实际拼写为准（官网自身可能拼错，见踩坑 3） |
| ECVA（ECCV） | WebSearch `ecva.net 标题` | 先拿到 `.../html/1315_ECCV_2022_paper.php`，**PDF 文件名与页面编号不同**（实际是 `.../papers/136990295.pdf`），必须从 php 页里提取真实链接 |
| NeurIPS | WebSearch `proceedings.neurips.cc 标题` | `/paper_files/paper/YYYY/hash/<hash>-Abstract-Conference.html` → PDF 把 `hash/...-Abstract` 换成 `file/<hash>-Paper-Conference.pdf` |
| ICML / PMLR | 查 `https://proceedings.mlr.press/` 主页卷列表 | **卷会滞后**：当年 7 月开的会，9 月可能还没上线（ICML 2025 = v267）。未上线 → 记 OpenReview 论坛页 + icml.cc 虚拟页，注明待 PMLR |
| arXiv | abs 页 `arxiv.org/abs/<id>` 一站三格式 | PDF：`arxiv.org/pdf/<id>`；HTML：`arxiv.org/html/<id>`（2023-12 后有原生 HTML），旧论文走 `ar5iv.labs.arxiv.org/html/<id>`（覆盖率高，公式渲染偶有瑕疵）；TeX 源码：`arxiv.org/e-print/<id>`（tar.gz，内含多文件，主 tex 需辨认） |
| IEEE（TIP/TPAMI） | WebSearch 标题 + ieeexplore | 默认只记：Xplore `https://ieeexplore.ieee.org/document/<id>/`、CSDL `computer.org/csdl/...`、DOI（文档给了就直接记）。Xplore 对 curl 返回 202/403 反爬，属正常，不代表链接失效；用户要求尽力时再搜作者主页版本 |
| ACM（MM 等） | WebSearch 标题 + dl.acm.org | 默认只记 DOI 页（如 `https://dl.acm.org/doi/10.1145/3581783.3612351`）。部分作者方（实验室官网）会挂公开 PDF，可搜 `标题 + pdf` |
| OpenReview | 记录论坛页 URL | 对 curl 一律 403（含 `/pdf?id=` 与 hash 直链，加浏览器头也没用），别恋战；浏览器中人工可开 |

### 4. TeX 源码与 HTML（arXiv 系默认带 TeX）

**arXiv 系论文一律在下载阶段先拿 TeX 源码**（`arxiv.org/e-print/<id>`，tar.gz）：TeX 本身就是良好的纯文本源，解压即交付（详见 to-source 子手册），不用等提取时再补。PDF 是面向"拿到论文"的默认交付物，按需再下；HTML（原生 `arxiv.org/html`，旧论文 ar5iv 兜底）用户点名要时再取。非 arXiv 系论文不为此额外找源码，提取时走 PDF-only 路径。

落盘到论文文件夹：`<论文全名>-src.tar.gz`；`<论文全名>.html`（按需）。tarball 不默认解压，提取阶段解压到 `tex-source/`，**解压验证成功后删除 tar 包**（`tex-source/` 自此即为源文件）。拿到的格式同样记入索引"下载内容"列（多值并列）。

### 5. 下载与验证（每个文件必做）

```bash
curl -sL -A "Mozilla/5.0" -o "ICCV2021_HOZ_Zhang/Hierarchical_Object-to-Zone_Graph_for_Object_Navigation.pdf" "<PDF直链>"
head -c 5 "ICCV2021_HOZ_Zhang/Hierarchical_Object-to-Zone_Graph_for_Object_Navigation.pdf"   # 必须输出 %PDF-
ls -la                                                   # 必须 > 100KB
curl -sI -A "Mozilla/5.0" "<PDF直链>" | grep -i content-length   # 与本地字节数对账，确认来源
```

源文件以论文全名命名（空格用 `_` 替代，标点保留或去掉以可读为准），如 `Hierarchical_Object-to-Zone_Graph_for_Object_Navigation.pdf`；后续 HTML、TeX 源码跟随同一主名。

- **绝不能把 HTML 存成 .pdf**：渠道被拦截时返回的 HTML 报错页只有 ~12KB，`<title>Error 403 | OpenReview</title>` 一查便知。发现就删除该文件，改记 URL。
- 非 PDF 格式同样验真：HTML 确认 `<title>` 或正文含论文标题、而非报错/登录页；TeX tarball 用 `tar -tzf` 能列出内容，排除空文件或报错页。
- 下载源 URL 必须留痕：subagent 报告里要有，否则事后无法写进索引。

### 6. 落盘与索引

- **下载即入库**：每篇成功的论文直接落成论文文件夹，源 PDF 以论文全名命名（空格用 `_`），不设平铺中转、不再搬家。
- 仅记 URL 的论文不建文件夹，信息只进索引行（下载内容列为空）。CVF 有补充材料的（`/supplemental/` 路径）把链接附在来源页列。索引表列结构见 SKILL.md 共享约定，示例行：

```markdown
| ICCV2021_HOZ_Zhang | https://openaccess...html | `ICCV2021_HOZ_Zhang/` | CVF PDF | 未开始 | 未阅读 |
| ... | https://ieeexplore.../ | — | — | — | — |
```

### 7. 汇报

先说结果（几篇成功、几篇只记 URL、各自原因），再列产出文件夹与库索引路径。

## 踩坑记录（防再踩）

1. **OpenReview 全面反爬**：对 curl 一律 403（含 `/pdf?id=` 和 hash 型 PDF 直链，加浏览器头也没用）。别恋战，记录 URL 即可，浏览器中人工可开。
2. **PMLR 卷滞后**：不要假设当年 ICML 已在 proceedings.mlr.press，先抓主页卷列表确认。
3. **CVF slug 拼写错误**：官网把 "Rearrangement" 拼成 "Rearrangment"，按正确拼写构造的 URL 会 404。构造失败就 WebSearch 或抓 abstract 页拿真实链接，别反复改拼写重试。
4. **ECVA 页面编号 ≠ PDF 文件名**（见速查表）。
5. **ACM/IEEE DOI 页 curl 返回 HTML 登录/校验页**，大小仅几 KB~几十 KB——未验证文件头就保存是最常见的假成功。
6. **重复引用**：申报书类文档常有同文两编号，去重后再分派，否则重复下载。
7. **Windows/Git Bash 细节**：中文路径和文件名没问题（cd 过去再操作更稳）；`/tmp` 可用；curl 记得 `-A "Mozilla/5.0"`；DNS 失败（exit 6）就换域名变体（有无 www）；本机 grep 是 ugrep，复杂 `{0,120}` 量词正则会报错，用简单模式或 python。
