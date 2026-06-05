# Transcript-led fallback session note — Gemini monthly spending cap

## Context

During a podcast deep-reading run for `wC0XcqX_k7Q`, `video_analyzer.py` successfully downloaded and uploaded the video, then failed at Gemini `generate` with:

`429 RESOURCE_EXHAUSTED ... exceeded its monthly spending cap`

This is a visual-analysis blocker, not a full article blocker, when reliable subtitles are available.

## Durable pattern

1. Mark Step 02 visual analysis as cancelled/blocked with reason: Gemini monthly spending cap.
2. Mark Step 03 screenshot extraction as cancelled/blocked; do not extract or insert unverified frames.
3. Continue with `scripts/get_transcript.py` and write a transcript-led article.
4. In the article/frontmatter, explicitly label quality as subtitle-led / no visual analysis.
5. Remove Step 07 image-placement work from the active path; run it as editorial review only.
6. Still run fidelity check against transcript, stable artifact copy, and Final Gate.
7. Final response must be transparent: no screenshots were used because visual analysis was blocked.

## Why this matters

For long podcast/interview content, subtitles can still support a responsible deep reading. The key safety rule is honesty: do not write visual claims, do not insert screenshot placeholders, and do not imply the agent inspected the footage when Gemini visual analysis did not complete.

## Final Gate nuance observed

`final_gate.py <file>` may perform normalization before failing on zh-en spacing. If that happens, fix spacing in the already-normalized stable file, then rerun `final_gate.py <file> --check-only` to verify. Avoid rerunning the non-check normalization repeatedly after manual language fixes, because it can reintroduce awkward term conversions.