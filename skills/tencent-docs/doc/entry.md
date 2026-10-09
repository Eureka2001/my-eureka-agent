# Word 文档（doc）品类操作指引

本目录提供 Word 文档（doc）品类的专业操作能力，包括公文、合同、通知、协议书等专业规范化文件的格式套用与美化。

## 功能

- **格式套用**: 将纯文本排版美化并导出为在线文档（Word格式）

## 使用场景

- 创建正式文档（通知、报告、公文、合同等）
- 将纯文本转换为格式与排版美化后的 Word 文档

## 可用模块

### 格式套用模块 (`doc_format`)

将纯文本转换为排版美化后的文档。

## 工作流程

**执行前必须:**

1. **阅读相关文档(`doc/doc_format/README.md`)**
2. **理解工作流程**
3. **执行各步骤**

## 相关工具

使用 `tencent-docs` MCP Server 中的 `doc.*` 系列工具执行读写、美化等操作。工具参数以会话内 `tools/list` 实时 Schema 为准。

## 已知边界（2026-10-09 实测主端点；实际行为与记录不符时当场更新本节）

**做不了的（无工具 / 字段失效，不要绕道）：**

- ❌ **首行缩进（字符单位）**：`modify_paragraph` 的 `first_line_indent` / `first_line_indent_chars`（含 `has_*` 开关）均被引擎丢弃（报 "ModifyParagraphOp: at least one property must be set"）；`insert_html_content` 的 `text-indent:2em` 会被固化为绝对值（实测 0.85cm）而非 2 字符——两条路都不等价。需要字符级首行缩进的文档改用智能文档（smartcanvas）品类
- ❌ **合并单元格**：doc 工具集无 merge 工具（slide 品类才有 `slide_merge_table_cells`）
- ❌ **原生公式（OMath）**：无工具
- ❌ **表格列宽/行高调整**：`set_table_layout` 引擎未实现（返回 tool not found）；列宽仅能随 `set_table_properties` 的整体设置或保持 auto
- ❌ **单元格垂直对齐**：无工具（水平对齐可用 `modify_paragraph` 的 `jc` 作用于 cell 内段落实现，实测有效）
- ❌ **图片紧邻段的文本属性**：含图片锚点控制符（`\u0005`）的段落，`update_text_property` 任意范围均报 "TextValidator cannot find p parent"，段落级 `jc` 不受影响

**行为约束（踩过的坑）：**

- ⚠️ **`update_text_property` 禁止跨段大范围**：报 "cannot find p parent" / "should have rpr"。正确做法：按段落取**段内范围（不含段尾符）**，用 `ranges` 数组一次批量提交多段（实测单调用 16 段成功）
- ⚠️ **文档以表格结尾时无法在其后插入**：`get_last_operable_pos` 落在表内（报 "inside a table structure"），+1 又越界。保证文档末尾留一个空段落，或把新内容插到表格前
- ⚠️ **结构性插入会移动后续所有索引**：插入后用返回的 `last_index` / `next_index` 锚定，或重新 `resolve_document_structure`；同一批多个插入按目标索引**从右到左**提交可免重算
- ⚠️ **run 级子范围先数字符**：做上下标、局部高亮等子范围操作前，先按 `resolve_document_structure` 的 `text_preview` 或 `get_content` 数清目标字符在段内的位置（UTF-16 语义），避免样式打到相邻字符上
- ⚠️ **`set_page_number` 与 `insert_footer` 互斥**：设置页码会清空已有页脚文本；`scope` 合法值是 `whole_doc` / `from_here` / `current_section`（不是 `whole_document`）
- ⚠️ **`highlight_block` 与代码块都是 TextBox 节点**：`resolve_document_structure` 里显示为 `[TextBox]`，其内容不参与普通段落的文本索引语义
- ⚠️ **`insert_image` 大图走本地直连**：base64 经 MCP 通道会撑爆 agent 上下文。用 skill 根目录的 `mcp_call.js` 模块（`require` 后 `callMcp("doc.insert_image", {...})`）在本地插入；宽高不会自动等比，需按图片原始宽高比自行计算

**实测可用的能力清单**（均已在测试文档验证）：标题层级（H1-H4）、粗/斜/下划线/删除线/颜色/高亮/底纹/字号/上下标、五种对齐（left/center/right/both/distribute）、行距（倍数/exact 固定值）、段前段后距、整段缩进（increase/decrease）、引用块、高亮块、项目符号/编号/待办列表、代码块、超链接、脚注、批注、格式刷、分隔线、分页符、页眉、页脚、页码、查找/替换、markdown 批量导入（含表格）、表格（插入/行列增删/边框/条件底纹/内边距/整表对齐/单元格水平对齐/单元格写入）、图片插入与题注段落。
