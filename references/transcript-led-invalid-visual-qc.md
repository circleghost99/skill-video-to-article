# Transcript-led fallback when visual extraction / QC yields zero usable assets

## Trigger

Use this when the full v2a pipeline starts normally, but Step 02/03 does not produce trustworthy visual assets:

- Gemini returns `key_frames: []` or only weak / sparse visual candidates.
- `extract_assets.sh` fails because `key_frames` is empty while `gif_segments` exists.
- Asset QC shows the extracted frame/GIF is a talking-head or otherwise does not match Gemini's expected UI / slide / search-page description.
- Candidate offsets such as ±1s / ±2s still do not recover a valid visual.

This is different from Gemini quota failure. Visual analysis may have completed, but the concrete media evidence is not usable.

## Required behavior

1. **Do not fabricate visuals.** Do not synthesize a screenshot entry just to satisfy `extract_assets.sh`, and do not keep a frame/GIF that QC says is mismatched.
2. Mark Step 03 as cancelled / blocked with an explicit reason such as: `無可用實體截圖，改 transcript-led 文字解讀`.
3. Continue with Step 04 transcript acquisition if captions are usable.
4. Treat Step 07 as editorial review only:
   - Do not enforce the minimum image count.
   - Do not insert Markdown images or placeholders.
   - Verify no visual claims remain: `畫面顯示`, `如圖`, `截圖`, `圖片`.
5. In frontmatter / handoff, be transparent, e.g. `quality_badge: "🟢 英文人工字幕，transcript-led，視覺素材 QC 未通過，正文不插入圖片"`.
6. Still run fidelity check and Final Gate as usual.
7. Stable preview should copy only article / fidelity / theme-map / transcript / analysis. Do not copy invalid `outputs/images` into final deliverables.

## `extract_assets.sh` empty-key-frame pitfall

Current extractor behavior can fail when `.analysis.key_frames | length == 0` because the shell loop expands `seq 0 -1` and then reads `.analysis.key_frames[0].timestamp` as `null`, causing arithmetic errors like:

```text
10#null: value too great for base (error token is "10#null")
```

If this happens, do **not** patch the analysis with invented key frames unless a real frame has already been visually verified. Prefer:

- Skip Step 03 and continue transcript-led when visuals are nonessential.
- Or manually extract a specific verified timestamp and QC it before adding it to a manifest.

## Why this matters

The visual standard is evidence-first. A deep reading can still be delivered responsibly from transcript, but fake or mismatched screenshots are worse than no screenshots because they make the article appear visually verified when it is not.