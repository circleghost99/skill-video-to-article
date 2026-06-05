# Conference batch text artifact gates

Session pattern captured from a Code with Claude London 2026 batch where the user requested Traditional Chinese articles for selected playlist indices and expected three stable artifacts per talk.

Use this when a conference-series run is **transcript-led** and the deliverable is not immediate Notion publishing, but a publish-ready text packet:

```text
articles/<NN-slug>.md
figures/<NN-slug>-figure-brief.md
reports/<NN-slug>-fidelity.md
```

## Manifest-first paths

- Treat `playlist_manifest.json` as the source of truth for index, slug, title, video URL, transcript path, article path, figure brief path, and fidelity report path.
- Do not create sidecar notes unless the manifest or user asked for them. If a temporary note is generated accidentally, delete it before final delivery.
- When working on selected indices, print or log the resolved paths for those indices before writing, so later validation does not chase inferred filenames.

## Figure briefs when no visual extraction ran

If this is a transcript-led batch and no Gemini/ffmpeg visual extraction was performed:

- Produce **figure briefs**, not actual embedded screenshots.
- Make each brief contain exactly the expected conceptual image sections, e.g. two `## 概念圖` blocks when the batch gate requires two concept diagrams.
- Include a concrete generation prompt marker such as `Codex prompt:` for each concept, so later image-generation agents can pick it up deterministically.
- Do not imply that the concept figure came from a real video frame.

## Fidelity reports

For batch text packets, require a compact evidence table per article:

- 8–12 numbered rows is a useful range; 12 rows gives enough coverage for long talks.
- Each row should distinguish transcript-supported facts from editorial interpretation.
- Avoid writing uncertain transcript noise as a firm claim. Use hedges such as「影片主張」「講者把它描述為」「這場 demo 呈現的是」when the exact term is noisy.

## Deterministic batch validator

After writing or patching, run one deterministic validator over every selected item. The useful gates from the session were:

- article exists
- CJK **body** length in the target band, e.g. 1800–2600 for compact publish-ready drafts. Count body after frontmatter only; do not let a long `hamster_note` mask an under-length body.
- frontmatter `hamster_note` CJK length in the expected band, e.g. 200–300. This is a separate gate from body length; if only the note fails, patch the note, not the article body.
- HTML tags = 0 across article / figure brief / fidelity report
- em dash / U+2015 = 0 across all artifacts
- article H1 count = 0
- body-only `---` divider count = 0. For YAML-frontmatter articles, the first two `---` lines are legal delimiters; count body dividers with `dividers[2:]`. Avoid line-number recomputation from `len(fm.splitlines())`, which can falsely flag the closing frontmatter delimiter.
- figure brief has the required concept-section count. Match the marker used by the artifacts for this batch (`## 概念圖` or `## Concept`), and keep the validator in sync with the template actually written.
- figure brief has matching `Codex prompt:` count
- fidelity report has required numbered evidence rows. Match the report schema actually written (`| 1 | ... |` table rows or `- item 1:` bullet rows); do not hard-code one schema if the batch template uses the other.
- frontmatter `hamster_note` may be written as YAML block scalar (`hamster_note: >`) or a one-line quoted/unquoted value. Batch validators should parse both shapes; otherwise a valid note can be miscounted as `0` and trigger unnecessary rewrites.
- In transcript-led batches, article image count may legitimately be `0` because actual screenshots were not extracted. Do not fail the article for zero images if the task explicitly produced figure briefs instead of embedded figures; validate the figure brief artifacts separately.

Example validator skeleton:

```python
import json, re
from pathlib import Path

manifest = Path('playlist_manifest.json')
data = json.loads(manifest.read_text())
selected = {15, 19, 20, 22}

for e in data['entries']:
    if e['index'] not in selected:
        continue
    article = Path(e['article_path'])
    fig = Path(e['figure_brief_path'])
    fid = Path(e['fidelity_path'])
    text = article.read_text()
    ftxt = fig.read_text()
    fidtxt = fid.read_text()

    parts = text.split('---', 2)
    fm = parts[1] if text.startswith('---') and len(parts) >= 3 else ''
    body = parts[2] if len(parts) >= 3 else text

    cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
    html = len(re.findall(r'<[^>]+>', text))
    all_html = len(re.findall(r'<[^>]+>', text + ftxt + fidtxt))
    emdash = sum(ch in '\u2014\u2015' for ch in text + ftxt + fidtxt)
    h1 = sum(1 for line in text.splitlines() if line.startswith('# '))
    dividers = [i for i, line in enumerate(text.splitlines(), 1) if line.strip() == '---']
    body_divider = dividers[2:]
    note_match = re.search(r'hamster_note:\s*\|\n((?:  .+\n?)+)', fm)
    note_cjk = len(re.findall(r'[\u4e00-\u9fff]', note_match.group(1) if note_match else ''))
    fig_concepts = ftxt.count('## 概念圖')
    prompts = ftxt.count('Codex prompt:')
    fid_rows = len(re.findall(r'^\| \d+ \|', fidtxt, re.M))

    basic = 1800 <= cjk <= 2600 and html == 0 and h1 == 0
    extended = (basic and not body_divider and 200 <= note_cjk <= 300
                and fig_concepts == 2 and prompts == 2
                and 8 <= fid_rows <= 12 and all_html == 0 and emdash == 0)
    print(e['index'], 'BASIC', 'PASS' if basic else 'FAIL',
          'EXTENDED', 'PASS' if extended else 'FAIL',
          dict(cjk=cjk, note_cjk=note_cjk, fig_concepts=fig_concepts, fid_rows=fid_rows))
```

## Patch loop discipline

- If one item misses only a narrow gate, patch the smallest relevant field instead of rewriting the whole article.
- If the body CJK count is just under the lower bound, add one grounded concluding or transition paragraph to the article body. If only `hamster_note` is short, expand only the note. Keep these two repairs separate because the validator should count them separately.
- When a gate misses by only 1–5 CJK chars (e.g. body 1797/1800 or `hamster_note` 199/200), do a surgical append of a short grounded phrase/sentence to the exact failing section, then rerun the validator once. Do **not** rerun an identical failing validator command without changing the artifact; inspect the metric and patch the failing field first.
- For `hamster_note` length failures, do not pad with generic meta-commentary. Append one concrete, grounded personal sentence tied to the talk's distinctive mechanism (e.g. 「一週內拆掉錯功能」, 「把 Word 變成 agent 能讀、改、驗證的環境」). Then re-run the same batch validator.
- Re-run the full selected-item validator after every patch that affects a gate, because a fix to `hamster_note` or frontmatter can shift another count.
- When validating `source_url`, prefer the manifest field actually present for the batch. Some manifests use `url` rather than `source_url`; do not let a validator falsely fail with `source_ok=False` because it checks a missing key. Use `source = e.get('source_url') or e.get('url')`, then verify the article frontmatter contains that exact URL.
- If a batch fails only on body CJK length after artifacts already exist, add one short transcript-grounded paragraph near the relevant section instead of padding with generic summary. Examples from the Code with Claude batch: add `post validation` after the Base44 bottleneck section, or add Spotify’s instrumentation / PR-review-pressure paragraph after the engineering-practices section.
- Final user response should include artifact paths and the **actual validator output summary**, not just “looks good.”
