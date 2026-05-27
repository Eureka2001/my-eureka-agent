---
name: trace-codechain
description: Trace a function call chain through the codebase and dump all user code into a single Markdown file for external AI debugging. Use when the user asks to "整理链路代码", "trace the pipeline", "dump call chain", or wants a consolidated code document for debugging.
user-invocable: true
argument-hint: <file-or-file:function>
---

# Trace Codechain

`$ARGUMENTS` specifies the entry point. Two forms are accepted:

- **File only**: `scripts/render_test.py` — starts from the file's main entry function (e.g. `main`, `if __name__`).
- **File + function**: `src/glmap/glmap.py:render_instances` — starts from the specified function only.

Trace the **complete call chain** from that entry point through user code, and produce a single Markdown file containing every user-code file involved.

## Instructions

1. **Parse the entry point** from `$ARGUMENTS`:
   - If it contains `:`, split into file path and function name. Start tracing from that specific function.
   - Otherwise, treat as a file path. Read it and find the main entry function (`main`, `if __name__ == "__main__"`, or the top-level call).

2. **Trace the call chain** by recursively reading imports and function calls within the project (`src/`). Follow every user-code dependency. Skip third-party / stdlib imports.

3. **Generate the Markdown file** with this structure:

   - Header: project name, purpose, one-line call chain overview
   - Table of contents linking to each file section
   - One section per file, ordered by call depth (entry first):
     - File path as heading
     - Complete file content in a fenced code block with language tag
   - Appendix: any reference tables (e.g., coordinate systems, data formats) that help understanding

4. **Write the file** to `scripts/` or the location the user specifies, named descriptively (e.g., `render_pipeline.md`).

5. **Keep it focused**: only include files that participate in the call chain. Do not include files that are imported but never called in the traced path. However, if a file is part of the data flow (e.g., serialization/deserialization), include it.

6. **Preserve code exactly** — copy source verbatim, do not paraphrase or summarize the code itself. Use comments only in section headings or the appendix.

## Output

Report to the user:
- How many files were traced
- The output file path
- A brief one-line summary of the call chain
