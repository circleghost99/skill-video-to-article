# Conference / event video series batch deep-reading workflow

Use this reference when the user asks for an entire conference or event video series to be found, interpreted, illustrated, and prepared for Notion/Obsidian. Example trigger:「Anthropic Code with Claude 大會釋出了一系列演講，請幫我找出來，並派 sub agent 逐篇進行深度解讀，然後配圖，由你來做品質管控。」

This is a **series orchestration** mode, not a single-video v2a run. It can use transcript-led article writing when the goal is to process many talks consistently and quickly.

## Recommended stable workspace

Create one durable workspace under the hamster profile, not `/var/folders`:

```text
/Users/circleghost/.hermes/profiles/hamster/outputs/<event-series-slug>/
  playlist_manifest.json
  transcripts/
  articles/
  figures/
  reports/
  illustrations/
  series_qc_report.md
```

The manifest is the source of truth for title, URL, video ID, index, slug, transcript path, article path, figure brief path, and fidelity report path. Do not infer YouTube IDs from titles or filenames.

## Orchestration pattern

1. **Discover the official series**
   - Prefer official channel / playlist / event page.
   - Write `playlist_manifest.json` with verified URLs and IDs.
   - If an item cannot be verified, mark it `source_url_verified: false` and do not fabricate a URL.

2. **Fetch transcripts and metadata**
   - Store transcript text and, if available, JSON metadata per video.
   - If a transcript is one long Whisper line, create semantic chunks for evidence citations while preserving the original transcript.

3. **Delegate article batches**
   - Split videos into small batches for `delegate_task`; each child writes only stable artifacts and returns a compact summary.
   - Each video should produce:
     1. `articles/<NN-slug>-analysis.md`
     2. `figures/<NN-slug>-figure-brief.md`
     3. `reports/<NN-slug>-fidelity.md`
   - In the child prompt, require it to load `video-to-article` and `hamster-writing-craft`, verify source URL from manifest, and cite transcript line/chunk evidence in the fidelity report.

4. **Main-agent QC pass**
   - The main agent owns quality control. Do not trust child self-reports as final.
   - Run artifact-level checks across every article, figure brief, and fidelity report:
     - HTML tags = 0
     - em dash / U+2015 = 0
     - article H1 = 0
     - illegal body `---` dividers = 0
     - `source_url_verified` present or the verified source URL is traceable to manifest
     - figure brief has concrete image keys / layouts
     - fidelity report includes evidence ranges
   - Write `series_qc_report.md` with pass/fail per item and unresolved caveats.

5. **Illustration phase is a separate gate**
   - Treat article QC and illustration QA as separate gates. Passing article final gate does **not** mean the series can publish.
   - Generate or collect illustrations into `illustrations/` only after text artifacts are stable.
   - Produce a contact sheet and OCR/vision QA report for all images.
   - If any illustration has suspected fake text, Simplified Chinese, English residue in all-TC images, watermark overlap, or broken layout, stop before Notion/Obsidian and report the issue. Do not publish just because article text passed.

6. **Delivery policy**
   - For a large series, first deliver a concise status report: number of talks processed, artifact paths, QC pass/fail, and exact blockers.
   - Only publish to Notion/Obsidian after both article final gate and image QA pass, or after the user explicitly approves publishing without images / with known caveats.

## Sub-agent prompt skeleton

```text
You are writing one batch of a conference video series deep reading in Traditional Chinese.
Workspace: <absolute series dir>
Manifest: <absolute playlist_manifest.json>
Items: <indices/slugs>

Load skills:
- video-to-article
- hamster-writing-craft

For each item:
1. Read the manifest row first; source URL and cover must come from the manifest, never from memory.
2. Read transcript text; if line structure is poor, cite semantic chunks.
3. Write article, figure brief, and fidelity report to the specified paths.
4. Body starts at H2, no H1, no HTML tags, no em dash.
5. Fidelity report must distinguish transcript-supported facts from interpretation.
Return only compact status: paths, source_url_verified yes/no, and blockers.
```

## Reporting language

Be explicit about gates:

- ✅ `20/20 articles passed text final gate`
- ⚠️ `10/20 illustrations have OCR/legibility flags`
- ❌ `Notion/Obsidian not published yet because image QA is not clean`

This avoids the common failure mode where a series sounds “done” after text QC even though publish-blocking image QA remains.
