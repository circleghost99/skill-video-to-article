# Visual resume after transcript-led v2a draft

Use this when a v2a run first continued as transcript-led because Gemini visual analysis was blocked, then the user fixes quota/billing and asks to resume visuals. The goal is to add verified video evidence frames/GIFs without rewriting the article from scratch.

## Resume contract

1. Keep existing text artifacts: `article_draft.md`, `transcript_clean.txt`, `notes_theme-map.md`, `fidelity_check.md`.
2. Re-run Step 02 against the already downloaded local video if available, not the original YouTube URL:

```bash
set -a; source /Users/circleghost/.hermes/.env >/dev/null 2>&1 || true; set +a
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/video_analyzer.py \
  "/ABS/WORKDIR/video_source.mp4" \
  -o analysis.json \
  --strip-audio \
  --keep-file \
  --model gemini-2.5-flash
```

3. Read back `analysis.json`: summary, duration, local video path, token/cost, key frame count, GIF count, and a small sample of frames.
4. Extract assets. If `extract_assets.sh` exits early but `analysis.json` contains valid timestamps, use the manual ffmpeg extraction fallback from `references/local-video-visual-retry-and-manual-assets.md`. This is a recovery path, not a reason to abandon visual evidence.
5. Build contact sheets that include *all* candidate frames and GIF first/last frames. Do not rely on a helper that only shows the first four images.
6. Delegate vision QA against the contact sheets. Filter the manifest down to a small evidence set, usually 5–10 assets. Prefer frames that prove article claims: title/topic, protocol overview, Q&A prompts, codelab UI, and one representative quiz result. Drop low-information title cards, speaker lists, repeated quiz option pages, pure transitions, and talking-head-only frames.
7. If the published/stable article copy was edited during transcript-led delivery, copy that stable article back into the active workdir before image placement, so you do not accidentally insert images into an older draft.
8. Run Step 07 as image placement only: remove any public no-image/transcript-only caveats, keep `quality_badge` for subtitle quality, insert absolute local image paths near matching paragraphs, and enforce no consecutive images.
9. Run Final Gate after image insertion.
10. Stable-copy `article_draft.md`, `analysis.json`, `manifest.json`, `contact_sheet.jpg`, `gif_contact_sheet.jpg`, `fidelity_check.md`, and `outputs/images/` into `/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/<VIDEO_ID>/`, then rewrite image paths in the stable article to the stable image directory and run Final Gate `--check-only` again.

## Reporting

Be explicit in the final handoff:
- Gemini visual analysis resumed successfully after quota/billing was fixed.
- How many candidate frames/GIFs were found.
- How many assets survived vision QA.
- How many evidence assets were inserted into the article.
- Final Gate result and stable artifact paths.

Do not claim the original transcript-led article was visually verified until the resumed visual pass, contact-sheet QA, and image-path stable copy have actually completed.