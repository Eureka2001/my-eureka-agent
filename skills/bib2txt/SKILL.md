---
name: bib2txt
description: Convert BibTeX (.bib) files to formatted citation text using pandoc and a CSL style file. Use this skill whenever the user wants to convert .bib files to formatted references, generate citation lists from BibTeX, format bibliography entries, or mentions anything about citation formatting, reference lists, or bibliography conversion — even if they don't explicitly name the file types.
---

# bib2txt — BibTeX to Formatted Citation Text

This skill converts a BibTeX (`.bib`) file into a plain-text formatted reference list using **pandoc** with a **CSL (Citation Style Language)** file to control the output format.

## Prerequisites

- **pandoc** must be installed and available on `PATH` (version >= 3.0 recommended).
- A `.bib` file (BibTeX bibliography).
- A `.csl` style file (Citation Style Language). A bundled default is provided at `assets/china-national-standard-gb-t-7714-2015-numeric.csl` (Chinese national standard GB/T 7714-2015 numeric style).

## Arguments

The skill accepts arguments as a space-separated string:

```
<bib_file> [csl_file]
```

- **bib_file** (required): Path to the `.bib` file.
- **csl_file** (optional): Path to a `.csl` style file. Defaults to the bundled `china-national-standard-gb-t-7714-2015-numeric.csl`.

If the user only provides a `.bib` file (or no arguments at all), use the bundled CSL default.

## How to Convert

The core conversion is a three-step process: extract citation keys from the `.bib` file, generate a temporary Markdown file that references all of them, then run pandoc with citeproc.

### Step 1: Read the .bib file to identify all citation keys

Parse the `.bib` file to extract every `@type{key, ...}` entry key. These are the identifiers between the `{` and the first `,` after each entry type (e.g., `@article{smith2023,` has key `smith2023`).

### Step 2: Build a temporary Markdown input

Create a temporary `.md` file containing a YAML frontmatter block (with an empty `references` field) and a single line that cites all keys in pandoc's citation syntax:

```markdown
---
references:
---

[@key1; @key2; @key3]
```

This ensures every entry in the `.bib` file appears in the output bibliography.

### Step 3: Run pandoc

Execute pandoc with the following flags:

```bash
pandoc <temp_md_file> \
  --citeproc \
  --csl="<csl_file>" \
  --bibliography="<bib_file>" \
  -t plain \
  --columns=1000 \
  -o "<output_file>"
```

Where:
- `<temp_md_file>` is the temporary Markdown from Step 2.
- `<csl_file>` is the CSL style file path (default: `assets/china-national-standard-gb-t-7714-2015-numeric.csl` relative to this skill directory).
- `<bib_file>` is the input `.bib` path.
- `<output_file>` defaults to the same name and directory as the `.bib` file, but with a `.txt` extension (e.g., `refs.bib` → `refs.txt`).
- `--columns=1000` sets the output line width. Pandoc's `-t plain` writer defaults to a column width of **72 characters** and will hard-wrap long bibliography entries across multiple lines, which breaks the one-entry-per-line format most users expect. Setting this to a large value (e.g., 1000) ensures each reference stays on a single line. If the user explicitly wants wrapped output, remove this flag or lower the value.

### Step 4: Clean up

Delete the temporary Markdown file. Then read the output `.txt` file and present its contents to the user.

### Step 5: Explain the CSL style and alternatives

After presenting the formatted output, briefly inform the user about the CSL file that was used for formatting. This helps users understand why the output looks a certain way and how they can change it.

Specifically, tell the user:

1. **Which CSL file was used** — name the file (e.g., "本次转换使用了 `china-national-standard-gb-t-7714-2015-numeric.csl`，即中国国家标准 GB/T 7714-2015 数字编号格式。").
2. **How to get other formats** — explain that if they need a different citation style (e.g., APA, IEEE, Chicago, Vancouver, author-year format, etc.), they can:
   - Download the corresponding `.csl` file from the **Zotero Style Gallery** (<https://www.zotero.org/styles>) or the **CSL styles repository** (<https://github.com/citation-style-language/styles>), then pass the file path as the second argument.
   - For Chinese-specific variants, check <https://github.com/daffywen/Chinese-STD-GB-T-7714-related-csl>.
   - Temporarily modify the existing `.csl` file for small tweaks (e.g., changing sort order, adding/removing fields) — CSL files are XML and can be edited with any text editor.
3. Keep this explanation concise — 2–3 sentences is enough. The goal is to make the user aware that the format is configurable, not to overwhelm them with details.

## Output Format

The output is a plain-text file with numbered references formatted according to the chosen CSL style. For example, with the GB/T 7714-2015 numeric style:

```
[1] ZHOU K, ZHENG K, PRYOR C, 等. Esc: Exploration with soft commonsense constraints for zero-shot object navigation[C]//International Conference on Machine Learning. PMLR, 2023: 42829-42842.

[2] YIN H, XU X, WU Z, 等. Sg-nav: Online 3d scene graph prompting for llm-based zero-shot object navigation[J]. Advances in Neural Information Processing Systems, 2024, 37: 5285-5307.
```

Type markers follow the Chinese national standard convention:
- `[J]` — journal article
- `[C]` — conference paper
- `[D]` — dissertation
- `[M]` — book
- `[R]` — report
- `[S]` — standard
- `[P]` — patent
- `[N]` — newspaper article

## CSL Styles

This skill bundles the **GB/T 7714-2015 numeric** style (`china-national-standard-gb-t-7714-2015-numeric.csl`) as the default, which is the Chinese national standard for bibliographic references.

If the user needs a different citation format (e.g., APA, IEEE, Chicago, Vancouver, etc.), they can download the corresponding `.csl` file from the **Citation Style Language** repository:

- **Repository**: <https://github.com/citation-style-language/styles>
- **Unofficial Repository**: <https://github.com/daffywen/Chinese-STD-GB-T-7714-related-csl>
- **Searchable gallery**: <https://www.zotero.org/styles>

When a user provides a custom `.csl` file path, pass it as the second argument / `--csl` flag value instead of the bundled default.

## Error Handling

- If pandoc is not installed, inform the user and provide the install URL: <https://pandoc.org/installing.html>.
- If the `.bib` file has syntax errors, pandoc will report them — relay the error message to the user.
- If no citation keys are found in the `.bib` file, inform the user that the file appears empty or malformed.
