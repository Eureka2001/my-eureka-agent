---
name: zh2en
description: Translate all Chinese content (comments, docstrings, strings, variable names) in the specified files to English. Use when the user asks to "translate", "中文转英文", "清理中文", or wants to remove Chinese content.
user-invocable: true
argument-hint: <file-pattern-or-path>
---

# zh2en — Translate Chinese to English

`$ARGUMENTS` specifies the target. Accepted forms:

- **Single file**: `src/glmap/config.py`
- **Glob pattern**: `src/gaussian/*.py`
- **Directory**: `src/glmap/fusion/` (all `.py` files recursively)

Scan every matched file and translate **all Chinese content** to English. This includes:

1. **Comments** (`#` and block comments)
2. **Docstrings** (single/double/triple quoted)
3. **String literals** (log messages, error messages, format strings, user-facing text)
4. **Variable/function/class names** only if they contain pinyin or Chinese characters
5. **Type annotation hints** or inline documentation

## Instructions

1. **Resolve the target** from `$ARGUMENTS`:
   - If a file path, process that file.
   - If a glob pattern, expand and process all matching files.
   - If a directory, find all `.py` files recursively under it.
   - If `$ARGUMENTS` is empty, process all `.py` files under `src/`.

2. **For each file**, read it completely, then systematically translate:
   - Preserve the exact structure, indentation, and formatting.
   - Keep technical terms accurate (e.g., coordinate system names like "COLMAP", "Agent" should not be changed).
   - Log messages: translate meaning, keep formatting placeholders (`%s`, `{}`, f-strings).
   - Error messages: translate meaning, keep structure.
   - Docstrings: translate to idiomatic English, keep RST/Google-style formatting if present.

3. **Do NOT change**:
   - Third-party API names or identifiers
   - Configuration key names (e.g., `MAP_RESOLUTION`) even if the comment above them changes
   - Coordinate system abbreviations (xFyLzU, xRyDzF, xRyUzB)
   - Project-specific terminology that is already in English

4. **Write the updated file** in place.

5. **Run `pre-commit run --all-files`** after all files are processed to ensure formatting stays consistent.

## Output

Report to the user:
- How many files were processed
- A brief summary of what was translated (comments, docstrings, strings, etc.)
