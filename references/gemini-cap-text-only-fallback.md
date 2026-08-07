# Gemini spending-cap fallback: transcript-led article

When `video_analyzer.py` fails with `429 RESOURCE_EXHAUSTED` caused by a Gemini monthly spending cap, treat this as a visual-analysis blocker, not a full v2a blocker. This applies whether the cap appears during File API upload or later during `generate`; do not assume `analysis.json` or a reusable Gemini file URI exists.

## Decision rule

If the user asked for a deep reading / article and usable captions are available, continue as a **transcript-led deep reading** instead of stopping the whole task.

Do not retry the same Gemini call repeatedly. The fix is billing-cap management, not sleeping. If the failure occurred during upload, proceed without `analysis.json` and without asset extraction; use `metadata.json` + complete captions as the source of truth.

## Required handling

1. Mark visual analysis and asset extraction as cancelled or blocked in todo, with an explicit reason: Gemini monthly spending cap.
2. Continue Step 04 transcript acquisition with `scripts/get_transcript.py`.
3. Treat Step 07 as **editorial review only** when Step 03 is blocked: do not ask the reviewer to insert images or enforce minimum image count; instead, verify there are no Markdown images, screenshot placeholders, or visual claims such as 「畫面顯示」/「如圖」/「截圖」.
3. Set the article/frontmatter quality badge transparently, e.g. `🟡 YouTube 自動字幕（英文）`.
4. Do **not** insert video evidence frames, screenshot placeholders, or describe slides/UI frames.
   - If the user explicitly asked for article 配圖, concept figures are allowed after the transcript-led draft and fidelity check. Use `references/transcript-led-concept-figure-handoff.md`: plan with `creative/baoyu-article-illustrator`, generate / QA through `hamster-image-generation`, and keep captions / alt text framed as conceptual explanations, not evidence from the video.
5. Do **not** write claims like「我看到畫面」or「畫面顯示」unless a later visual pass actually verifies them.
6. Add a short caveat in the article: the piece is mainly based on cleaned subtitles / auto captions.
7. Still run the normal writing flow: theme map → draft → editorial review (no image insertion) → fidelity check → Final Gate → stable preview artifacts.
8. If the user later wants images, resume Step 02/03 after Gemini quota/billing is fixed or after they provide manually verified frames.

## Why this matters

A spending-cap failure is not the same as “no source material.” In this session, captions were usable and the article could be completed responsibly as a text-only deep reading. The key safety constraint is honesty: no visual claims, no fake screenshots, no fabricated slide descriptions.