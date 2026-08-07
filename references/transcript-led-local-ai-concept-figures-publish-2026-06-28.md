# Transcript-led local-AI v2a with concept figures and Notion publish (2026-06-28)

Session pattern: YouTube deep reading + 配圖 + Notion upload. Gemini File API upload failed with `429 RESOURCE_EXHAUSTED` monthly spending cap before `analysis.json` existed, but YouTube auto captions were complete and usable.

## Reusable workflow

1. Treat Gemini spending cap as **visual-analysis blocker**, not article blocker.
   - Cancel Step 02/03 evidence-frame path.
   - Continue with `get_transcript.py`, theme map, writing craft draft, editorial review, fidelity check.
   - Do not make any visual claims such as「畫面顯示」「截圖」「如圖」.
2. If the user asked for 配圖, use **concept figures**, not video evidence frames.
   - Plan with `creative/baoyu-article-illustrator` style outline/prompts.
   - Generate and QA through `hamster-image-generation`.
   - Captions/alt text must describe conceptual explanation, not evidence from the video.
3. Codex batch generation can hang after valid artifacts are already written.
   - Verify existing PNGs first; do not discard them because the wrapper is still running.
   - Kill stalled batch if needed, then foreground-generate only missing/failed figures.
4. Contact sheet QA should ignore filename labels and judge the image body only.
   - If one image fails text QA, move it aside with a `*-fail-qa-*` suffix, patch only that prompt, regenerate only that figure, rebuild contact sheet.
5. After concept figures are inserted, rerun Final Gate and Notion preflight/publish.
   - Publish can write Cloudinary URLs back to Markdown; scan the written-back source again before Obsidian sync.

## Local-AI terminology pitfall

For this article class, `final_gate.py` / Notion preflight may convert「本地 AI」to「本機 AI」because of Taiwan term normalization. The session accepted remote publish because no hard bad-term list caught it, but the intended public terminology was **本地 AI**.

Future agents should do a semantic terminology pass after any zhtw/OpenCC conversion signal:

- If the article deliberately uses「本地 AI」as the main concept, scan local and remote output for「本機 AI」.
- Repair source naturally before publish/update if the term drift changes the article voice or title consistency.
- Add topic-specific scan terms instead of relying only on the generic OpenCC bad-term list.

## Verification checklist

- Transcript coverage: last timestamp near video duration.
- Article has no Markdown images before concept-figure insertion.
- After insertion: no consecutive images, every image path exists, captions are conceptual.
- Contact sheet QA: all PASS.
- Final Gate: pass.
- Preflight/publish: pass, `images_uploaded` equals inserted concept figures.
- Inspect: Notion manifest images equals Markdown image count.
- Blocks readback: block count nonzero, first/last paragraph present, image URLs are Cloudinary, captions present, bad terms including topic-specific terms are zero.
- Obsidian sync only after Cloudinary URL write-back; hash identity check source vs Obsidian copy.