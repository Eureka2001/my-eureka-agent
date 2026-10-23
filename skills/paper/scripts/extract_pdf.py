"""论文 PDF 确定性提取工具（skills/paper 的固定脚本）。

依赖声明在本目录 pyproject.toml（`uv sync` 建 .venv）；通过
`uv run --project <本目录> extract-pdf ...` 或 console-script 调用。

正文提取内核是 PyMuPDF 2.0 的 ``Document.to_markdown()``（布局感知：双栏阅读
顺序、标题层级、表格、斜体/加粗均由它处理）；本脚本只做编排——多文件批量、
按章节切分、参考文献切分、落盘路径。模型不临场编写提取代码。

用法：
    uv run skills/paper/scripts/extract_pdf.py extract <pdf>... [--write]
    uv run skills/paper/scripts/extract_pdf.py split <pdf>...
    uv run skills/paper/scripts/extract_pdf.py outline <pdf>...
    uv run skills/paper/scripts/extract_pdf.py refs <pdf>...

子命令说明：
    extract  输出整篇 markdown；--write 时写到 <PDF 所在目录>/markdown-source/paper.md
    split    按编号章节标题切成多个子 MD，写到 <PDF 所在目录>/markdown-source/
    outline  列出识别到的全部标题行
    refs     定位 References 后按 [N] 条目切分的初稿

所有子命令都接受多个 PDF；单文件失败不中断批次（错误进 stderr，退出码 1）。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Protocol

import pymupdf

FRONT_MATTER_NAME = "front-matter"
SLUG_MAX_LEN = 40
# 判定参考文献为 markdown 表格所需的表格行数下限
MIN_TABLE_ROWS = 3
NEXT_FILE_MARKER = "\n<!-- ======== next file ======== -->\n"
# to_markdown 的标题行形如 `## **1. Introduction** `（加粗装饰与尾随空格都可能出现）
HEADING_RE = re.compile(r"^(?P<level>#{1,6})\s+(?P<body>.*?)\s*$")
# 标题正文的编号前缀：阿拉伯多级（1 / 1. / 3.1）或罗马一级（I.）；编号与标题
# 之间可隔加粗记号（中文期刊输出形如 `# **1** 相关背景`）
SECTION_NUM_RE = re.compile(r"^\**(?P<num>\d+(?:\.\d+)*\.?|[IVXLC]+\.)(?=\**\s|\s|$)")
# 一级编号：`1`、`1.` 或 `I.`；`3.1` 一类子节不算
TOP_LEVEL_NUM_RE = re.compile(r"^\d+\.?$|^[IVXLC]+\.$")
REFERENCES_HEADING_RE = re.compile(
    r"^#{1,6}\s+(References|Bibliography|REFERENCES)\b.*$", re.MULTILINE
)


class PdfHandler(Protocol):
    """子命令处理器：处理单个 PDF，write 来自 --write 选项。"""

    def __call__(self, pdf_path: Path, *, write: bool) -> None: ...


def to_markdown(pdf_path: Path) -> str:
    """提取单个 PDF 为 markdown；文件缺失/损坏时由 pymupdf 抛异常，调用方记账。"""
    # Document.to_markdown 是 pymupdf 2.0 运行时挂载的 API（内部转调
    # pymupdf4llm.to_markdown(pdf_path)），静态类型不可见，故 ignore
    return pymupdf.open(pdf_path).to_markdown()  # type: ignore[attr-defined]


def heading_slug(title: str) -> str:
    """章节标题转文件名安全的短 slug（去编号前缀、压缩分隔符、限长）。"""
    text = re.sub(r"^#{1,6}\s+\**\s*(?:\d+(?:\.\d+)*\.?|[IVXLC]+\.)\**\s*", "", title)
    slug = re.sub(r"[^\w\-]+", "-", text).strip("-").lower()
    return slug[:SLUG_MAX_LEN].rstrip("-") or "section"


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[written] {path}", file=sys.stderr)


def cmd_extract(pdf_path: Path, *, write: bool = False) -> None:
    content = to_markdown(pdf_path)
    if write:
        write_markdown(pdf_path.parent / "markdown-source" / "paper.md", content)
    else:
        print(content, end="")


def top_level_boundaries(md: str) -> list[tuple[str, str]]:
    """找出一级编号章节标题，返回 (slug, 原始行)。

    各排版的标题层级不统一（有 h1 也有 h5），取命中最多的层级作为切分层，
    只按一级编号（`1.` / `I.`）切分，`3.1` 一类子节留在所属章节内。
    """
    candidates: list[tuple[int, str, str]] = []
    for line in md.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        num = SECTION_NUM_RE.match(m["body"].strip())
        if num and TOP_LEVEL_NUM_RE.match(num["num"]):
            candidates.append((len(m["level"]), heading_slug(m["body"]), line))
    if not candidates:
        return []
    level = Counter(c[0] for c in candidates).most_common(1)[0][0]
    return [(slug, line) for lv, slug, line in candidates if lv == level]


def cmd_split(pdf_path: Path, *, write: bool = False) -> None:
    """按编号章节标题边界切分，每章一个文件，写到 markdown-source/ 下。"""
    md = to_markdown(pdf_path)
    boundary_lines = {line for _, line in top_level_boundaries(md)}
    sections: list[tuple[str, list[str]]] = [(FRONT_MATTER_NAME, [])]
    for line in md.splitlines():
        if line in boundary_lines:
            sections.append((heading_slug(line), [line]))
        elif re.match(r"^#{1,6}\s+\**\s*(References|Bibliography|REFERENCES)\b", line):
            # 参考文献无章节编号，也作为独立切分边界
            sections.append(("references", [line]))
        else:
            sections[-1][1].append(line)
    out_dir = pdf_path.parent / "markdown-source"
    written = 0
    for index, (name, sec_lines) in enumerate(sections):
        if not any(line.strip() for line in sec_lines):
            continue
        write_markdown(
            out_dir / f"{index:02d}-{name}.md", "\n".join(sec_lines).rstrip() + "\n"
        )
        written += 1
    print(f"[split] {pdf_path.name}: {written} 个章节文件 → {out_dir}", file=sys.stderr)


def cmd_outline(pdf_path: Path, *, write: bool = False) -> None:
    for line in to_markdown(pdf_path).splitlines():
        if line.startswith("#"):
            print(line)


def cmd_refs(pdf_path: Path, *, write: bool = False) -> None:
    md = to_markdown(pdf_path)
    m = REFERENCES_HEADING_RE.search(md)
    if not m:
        raise ValueError("未定位到 References 小节")
    tail = md[m.end() :]
    table_lines = [
        line.strip() for line in tail.splitlines() if line.lstrip().startswith("|")
    ]
    # 表格形式的参考文献按行、正文形式按 [N] 前缀切分
    if len(table_lines) > MIN_TABLE_ROWS:
        entries: list[str] = table_lines
    else:
        entries = [
            entry.strip().replace("\n", " ")
            for entry in re.split(r"(?=\[\d+\]\s)", tail)
            if entry.strip()
        ]
    for entry in entries:
        print(entry, "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="论文 PDF 确定性提取工具")
    sub = parser.add_subparsers(dest="command", required=True)

    def register(name: str, help_text: str, handler: PdfHandler) -> None:
        subparser = sub.add_parser(name, help=help_text)
        subparser.add_argument("pdfs", nargs="+", type=Path, help="一个或多个 PDF 文件")
        subparser.set_defaults(handler=handler, write=False)

    register("extract", "整篇 markdown 提取", cmd_extract)
    register("split", "按章节切成多个子 MD（写盘）", cmd_split)
    register("outline", "列出识别到的标题行", cmd_outline)
    register("refs", "参考文献切分初稿", cmd_refs)
    # --write 只属于 extract：它改变的是输出目标（stdout → 落盘），其他子命令固定写盘
    sub.choices["extract"].add_argument(  # type: ignore[index]
        "-w",
        "--write",
        action="store_true",
        help="写到 <PDF 所在目录>/markdown-source/paper.md",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return_code = 0
    for i, pdf_path in enumerate(args.pdfs):
        if i and args.command != "split" and not args.write:
            print(NEXT_FILE_MARKER)
        try:
            args.handler(pdf_path, write=args.write)
        except Exception as exc:  # noqa: BLE001 单文件失败不中断批次，错误进 stderr 便于汇总
            print(f"[失败] {pdf_path}: {exc}", file=sys.stderr)
            return_code = 1
    return return_code


if __name__ == "__main__":
    sys.exit(main())
