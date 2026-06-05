# Code with Claude series #24 artifact validation note

Session pattern from producing Code with Claude London 2026 index 24 (`What's new in Claude Code`) as a transcript-led three-artifact packet:

```text
articles/24-what-s-new-in-claude-code.md
figures/24-what-s-new-in-claude-code-figure-brief.md
reports/24-what-s-new-in-claude-code-fidelity.md
```

## Durable lessons

- Resolve paths from `playlist_manifest.json` first and print/use the manifest fields directly: `url`, `cover_image`, `transcript_path`, `article_path`, `figure_brief_path`, `fidelity_path`.
- For this Code with Claude batch, transcript ASR may write `Cloud` where the product is clearly `Claude`. It is acceptable to normalize to `Claude Code` in the article when the manifest title and talk context support it, but the fidelity report should explicitly disclose the ASR correction and keep evidence tied to transcript line numbers.
- If no visual extraction ran, the figure brief must stay concept-led: exactly two `## 概念圖` sections, exactly two `Codex prompt:` markers, and an explicit sentence saying these are not real video screenshots.
- Avoid H1 in support artifacts when using strict batch validators that scan all three files for `^# `. Use `## Fidelity report` or no top heading for figure briefs. This prevents a validator written to forbid article H1 from falsely failing due to figure/fidelity headings.
- `hamster_note` length is a separate gate from article body length. If only the note is short, patch the note with one grounded, task-specific reflection. Do not add generic padding or inflate the article body.

## Validator shape used

Useful checks for one selected item:

- article / figure / fidelity files exist
- article frontmatter contains exact manifest `url` and `cover_image`
- body CJK count in target band, counted after YAML frontmatter only
- `hamster_note` CJK count 200–300, counted from frontmatter only
- no HTML tags, no U+2014/U+2015, no body dividers, no H1 across the packet if the validator is strict
- figure brief has `## 概念圖` count = 2 and `Codex prompt:` count = 2
- fidelity report has 8–12 numbered evidence rows (`| 1 | ... |` table schema)

## Patch loop

If validation fails narrowly:

1. Inspect the failing metric before editing.
2. Patch only the failing section: note length → frontmatter note; body length → one transcript-grounded body paragraph; H1 failure → demote/remove support-file heading; evidence rows → fidelity table only.
3. Re-run the same validator once after the patch and report the actual output.
