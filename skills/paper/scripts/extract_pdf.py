# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf>=1.24"]
# ///
"""论文 PDF 确定性提取工具（skills/paper 的固定脚本）。

skill 文档里的"归栏拼装、页眉页脚去除、断词修复、页码标记"全部由本脚本完成，
模型不临场编写提取代码，只消费脚本输出做章节映射、校对与拼装。

用法（本仓库根目录或任意位置均可，uv 自动解析依赖）：
    uv run skills/paper/scripts/extract_pdf.py extract <pdf>            # 正文提取
    uv run skills/paper/scripts/extract_pdf.py outline <pdf>            # 章节候选行（字号启发式）
    uv run skills/paper/scripts/extract_pdf.py refs <pdf>               # 参考文献切分初稿

extract 输出（stdout，markdown）：
    - 每个物理页以 `<!-- pdf-page: N -->` 起始（从 1 起）；
    - 双栏按"左栏先右栏后"归栏（依据 block 的 x 坐标与页宽中点）；
    - 去除页眉页脚（页面上/下边缘的短孤立行、纯页码行）；
    - 修复跨行断词（行尾连字符）与多余换行；跨页段落衔接为同一段；
    - 页码信息保留在页标记注释里，供整理阶段按章节汇总，不逐段打印。

outline 输出：字号显著大于正文的独立短行，作为章节标题候选，供人工确认映射。

refs 输出：定位 References/Bibliography 起始页后按编号条目 [N] 切分的逐条列表。
"""

from __future__ import annotations

import re
import sys

import pymupdf

# 页眉页脚判定：距页边上/下 6% 以内、且长度不超过 90 字符的行
_EDGE_RATIO = 0.06
_MAX_EDGE_CHARS = 90
# 双栏分界容差：block 中点偏离页宽中点在此比例内视为可能跨栏，保守按单栏处理
_COLUMN_TOL = 0.08


def _is_edge_line(text: str, y0: float, y1: float, page_h: float) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if y1 < page_h * _EDGE_RATIO or y0 > page_h * (1 - _EDGE_RATIO):
        return len(stripped) <= _MAX_EDGE_CHARS
    if re.fullmatch(r"\d{1,4}", stripped):  # 装饰页码可能在边缘带以内
        return y1 < page_h * 0.12 or y0 > page_h * 0.88
    return False


def _page_blocks(
    page: pymupdf.Page,
) -> list[tuple[tuple[float, float, float, float], str]]:
    """返回过滤页眉页脚后的 (bbox, 文本) block 列表，双栏页按左栏先排序。"""
    blocks = [
        (b[:4], text)
        for b, text in (
            (blk[:4], blk[4].strip())
            for blk in page.get_text("blocks")  # type: ignore[index]
        )
        if text and not _is_edge_line(text, b[1], b[3], page.rect.height)
    ]
    if not blocks:
        return []
    mid = page.rect.width / 2
    # 双栏判定：多数 block 明确落在中线一侧才算双栏
    left = [b for b in blocks if b[0][2] < mid]
    right = [b for b in blocks if b[0][0] > mid]
    spanning = [b for b in blocks if b not in left and b not in right]
    if len(blocks) >= 4 and len(left) >= 2 and len(right) >= 2:
        # 左栏 → 右栏 → 跨栏块，各按纵坐标排；跨栏块（图表题等）放最后由模型辨认
        def y(b: tuple[tuple[float, float, float, float], str]) -> float:
            return b[0][1]

        return [*sorted(left, key=y), *sorted(right, key=y), *sorted(spanning, key=y)]
    return sorted(blocks, key=lambda b: (b[0][1], b[0][0]))


def _clean_text(raw: str) -> str:
    """块内文本清理：去软换行、修复断词、压缩空白。"""
    text = raw.replace("-\n", "")  # 跨行断词
    text = text.replace("\n", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def cmd_extract(pdf_path: str) -> None:
    doc = pymupdf.open(pdf_path)
    out: list[str] = [f"<!-- source: {pdf_path}; pdf-pages: 1-{doc.page_count} -->", ""]
    prev_tail = ""
    for i, page in enumerate(doc, start=1):
        page_lines: list[str] = [f"<!-- pdf-page: {i} -->"]
        for bbox, text in _page_blocks(page):
            clean = _clean_text(text)
            if not clean:
                continue
            # 跨页段落衔接：上一页末块未以句号/问号/叹号收尾且本块以小写开头
            if (
                prev_tail
                and not prev_tail.endswith((".", "?", "!", ":"))
                and clean[:1].islower()
            ):
                page_lines[-1] = page_lines[-1] + " " + clean
            else:
                page_lines.append(clean)
            prev_tail = clean[-40:]
        prev_tail = prev_tail if page_lines[-1] != f"<!-- pdf-page: {i} -->" else ""
        out.extend(page_lines)
        out.append("")
    print("\n".join(out).rstrip())


def cmd_outline(pdf_path: str) -> None:
    doc = pymupdf.open(pdf_path)
    sizes: dict[float, int] = {}
    for page in doc:
        for blk in page.get_text("dict")["blocks"]:  # type: ignore[index]
            for line in blk.get("lines", []):
                for span in line.get("spans", []):
                    t = span["text"].strip()
                    if t:
                        sizes[round(span["size"], 1)] = sizes.get(
                            round(span["size"], 1), 0
                        ) + len(t)
    if not sizes:
        return
    body_size = max(sizes, key=lambda s: sizes[s])  # 按字符量估计正文字号
    print(f"正文字号估计: {body_size}pt")
    for i, page in enumerate(doc, start=1):
        for blk in page.get_text("dict")["blocks"]:  # type: ignore[index]
            for line in blk.get("lines", []):
                spans = [s for s in line.get("spans", []) if s["text"].strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                size = max(s["size"] for s in spans)
                numbered = re.match(r"^(\d+\.?\d*\.?\s+|[A-Z]\d*\s+)", text)
                if (
                    size > body_size + 1.5
                    and len(text) < 90
                    and (numbered or size > body_size + 3)
                ):
                    print(f"p{i}\t{size:.1f}pt\t{text}")


def cmd_refs(pdf_path: str) -> None:
    doc = pymupdf.open(pdf_path)
    text = "\n".join(
        _clean_text(t)
        for page in doc
        for _, t in _page_blocks(page)
        if t.strip() and not _is_edge_line(t, 0, page.rect.height, page.rect.height)
    )
    m = re.search(r"\b(References|Bibliography|REFERENCES)\b", text)
    if not m:
        print("未定位到 References 小节", file=sys.stderr)
        sys.exit(1)
    tail = text[m.end() :]
    entries = re.split(r"(?=\[\d+\]\s)", tail)
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        if re.match(r"^\[\d+\]", entry):
            print(entry + "\n")
        elif entries.index(entry) == 0:
            print("(References 标题与首个条目之间的内容:)", entry, "\n")


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in {"extract", "outline", "refs"}:
        print(__doc__, file=sys.stderr)
        return 2
    {"extract": cmd_extract, "outline": cmd_outline, "refs": cmd_refs}[argv[1]](argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
