# Transcript-led series example: Code w/ Claude 第 N 篇

Session pattern captured: user asks for「Code w/ Claude 第 9 篇影片撰寫繁中深度解讀初稿與配圖方案」without restating the URL. This is a good fit for `references/transcript-led-draft-plus-figure-brief.md`, not the full Gemini visual pipeline, when a transcript file already exists.

## What worked

Use the existing series workspace and naming convention rather than creating a new scattered output directory:

```text
/Users/circleghost/.hermes/profiles/hamster/outputs/code-with-claude-2025/
  transcripts/09-prompting-for-agents---code-w--claude.txt
  articles/09-prompting-for-agents---code-w--claude-analysis.md
  figures/09-prompting-for-agents---code-w--claude-figure-brief.md
  reports/09-prompting-for-agents---code-w--claude-fidelity.md
```

If directory search comes back empty but the task clearly names a numbered series item, try the predictable transcript path before asking the user for the URL again. The transcript can be the source of truth for `duration`, key evidence, and figure briefs. In dot-prefixed Hermes output directories, content search/file search can occasionally return zero results even when the exact file exists; verify with the provided absolute path via `read_file`, or use a tiny Python `Path.iterdir()`/`os.walk()` terminal probe rather than assuming the workspace is empty.

### Source URL / video ID guardrail

Do **not** infer or hardcode `source_url` / `cover_image` from memory, search-result memories, title guesses, or a plausible-looking video ID when working from a numbered series transcript. Before writing frontmatter, read one of the stable metadata sources in the same workspace:

1. `playlist_manifest.json` for the matching index / slug, or
2. the paired transcript JSON (`transcripts/<slug>.json`) if it contains video URL / ID metadata, or
3. an existing series index file if it records the URL.

Only then fill:

```yaml
source_url: "https://www.youtube.com/watch?v=<verified_id>"
cover_image: "https://img.youtube.com/vi/<verified_id>/maxresdefault.jpg"
```

If no metadata file verifies the ID, set `source_url: "TBD"` and `cover_image: ""` or `cover_image: "TBD"`, then mention the caveat in the final response. A transcript filename, title, or previous memory of the series is not proof of the YouTube ID.

**Hard stop before writing article:** if the task came from a bare numbered request like「第 17 篇」and you have not read either `playlist_manifest.json` or `transcripts/<slug>.json`, do not populate a YouTube URL. Add a quick QC line after writing: `source_url_verified: yes/no (<metadata file path or TBD>)`. This prevents otherwise good drafts from silently carrying wrong video IDs.

### Regression note: plausible YouTube IDs are still wrong

In a later numbered Code w/ Claude run, the draft was otherwise useful but the agent filled `source_url` and `cover_image` with a plausible-looking YouTube ID without reading metadata. Treat this as a release-blocking regression, not a harmless caveat. If metadata lookup is unavailable inside the allowed tool budget, write:

```yaml
source_url: "TBD"
cover_image: "TBD"
```

and include `source_url_verified: no (metadata not checked)` in the final QC. Never let a guessed ID enter stable artifacts, because downstream Notion covers and attribution will silently become wrong.

## Deliverable contract

For this class of request, create exactly three stable artifacts:

1. `articles/<slug>-analysis.md` — YAML frontmatter, body starts at H2, transcript-led caveat in frontmatter.
2. `figures/<slug>-figure-brief.md` — concept or screenshot brief; do not claim generated images or real screenshots exist.
3. `reports/<slug>-fidelity.md` — evidence table with transcript line ranges and nice-to-have items.

Final response should be concise and path-first: list the three files, QC summary, and caveats. Do not paste the whole article.

## Single-line Groq Whisper transcript pitfall

Some later Code w/ Claude items may have YouTube subtitles disabled and a Groq Whisper transcript saved as one long line. In that case, a fidelity report that only says `transcript:L1-L1` is technically true but not useful. Before writing the report, split the transcript into numbered semantic chunks in a temporary script output, and cite evidence as `transcript:L1, chunk NN` while preserving the original transcript path. Mention this caveat in the report source note. Keep the artifact count unchanged; do not create a separate normalized transcript unless the user asks.

## QC that caught issues

Run artifact-level QC across all three files, not just the article:

- article CJK / nonspace length
- H1 lines in article must be empty
- HTML tag count should be 0
- em dash / U+2015 count should be 0 across all files
- article body divider lines should be empty after excluding the two legal YAML frontmatter delimiters (typically lines 1 and frontmatter close)
- figure brief should contain concrete `image_key` entries and real layout instructions
- fidelity should include transcript line ranges
- final response should report `source_url_verified: yes/no`, not just paths and length

## Terminology note

English auto captions for Claude-related videos commonly mishear:

- Claude Code → Cloud Code / cla code / claw code
- Claude 4 → Cloud 4 / quad 4
- Agent → aent
- interleaved thinking → interled thinking

Normalize these in the article and figure brief, but preserve transcript line references in the fidelity report so the evidence remains traceable.
