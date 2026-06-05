# Code with Claude transcript-led batch notes

Session pattern: Code with Claude London 2026 playlist article packets where the source is a local transcript and the deliverable is three text artifacts, not immediate publishing:

- `articles/<NN-slug>.md`
- `figures/<NN-slug>-figure-brief.md`
- `reports/<NN-slug>-fidelity.md`

## Transcript normalization without overclaiming

Local ASR / transcript extraction may repeatedly misrecognize product names, e.g. `Cloud Code` for `Claude Code` or `Cloud` for `Claude`. In Code with Claude series work, normalize obvious series/product-name noise to `Claude` / `Claude Code` in the article, but make the fidelity report transparent:

> 字幕多次把 Claude 轉成 Cloud，本文依 Code with Claude 系列語境與產品名稱統一寫作為 Claude 或 Claude Code，但功能與流程描述均回到 transcript 行號支撐。

Do not use normalization to invent claims. Keep every feature/process claim tied to transcript line ranges.

## Artifact gates that caught real issues

For compact publish-ready drafts, run a deterministic validator and patch until it passes:

- body CJK count after frontmatter: 1800–2600
- `hamster_note` CJK count: 200–300
- article H1 count: 0
- body-only `---` divider count: 0
- HTML tags across all three artifacts: 0
- em dash / U+2015 across all artifacts: 0
- figure brief: exactly two `## 概念圖` sections and two `Codex prompt:` markers when batch requires two concepts
- fidelity report: 8–12 numbered evidence rows

Important implementation detail for body divider detection: for files with YAML frontmatter, the first two `---` lines are legal frontmatter delimiters. Count body dividers with `dividers[2:]`; do not try to recompute the closing-frontmatter line from `len(fm.splitlines())`, because small formatting differences can falsely flag the legal closing delimiter.

## Minimal patch loop examples

If only `hamster_note` is short, expand only the note with one concrete sentence tied to the talk’s mechanism. If only body CJK is short, add one grounded sentence or transition paragraph to an existing section. Re-run the full validator after every patch.

For Code with Claude #23, useful grounded body expansion came from the talk’s own mechanism: agent output velocity creates new bottlenecks at review, CI, docs, feedback, and merge maintenance unless loops/routines provide a new convergence mechanism.
