---
description: Mandatory KaTeX and LaTeX rendering safety protocol to permanently prevent UI parse errors across all workspaces.
trigger: always_on
---

# KaTeX & LaTeX Rendering Safety Protocol

To permanently prevent UI rendering errors (`Failed to render LaTeX: KaTeX parse error`), all agents across all workspaces MUST follow these strict formatting rules:

1. **NO Multi-Line LaTeX Environments:** NEVER use multi-line LaTeX math blocks or environments such as `\begin{aligned}`, `\begin{align}`, `\begin{matrix}`, `\begin{array}`, `\begin{split}`, or `\hline`. Markdown parsers frequently fragment these blocks, crashing the KaTeX renderer.
2. **Tabular Calculations & Statements -> Use Markdown Tables:** For all accounting reconciliations, financial statements, multi-step math additions/subtractions, and tabular layouts, ALWAYS use native Markdown tables or fenced code blocks. They render with 100% reliability, align columns cleanly, and never fail.
3. **NO Dollar Signs Inside LaTeX:** NEVER put literal `$` or escaped `\$` inside LaTeX math delimiters (`$$...$$` or `\(...\)`). In KaTeX, `$` is a syntax delimiter and will break the parser. Keep currency symbols in plain Markdown text outside the math delimiters.
4. **Single-Line Math Only:** Restrict LaTeX strictly to single-line display equations `$$ E = mc^2 $$` on their own isolated lines, or inline expressions `\( x = 5 \)`. Keep formulas simple, standard, and self-contained.
