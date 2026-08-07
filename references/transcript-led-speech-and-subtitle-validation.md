# Transcript-led speech / keynote mode and subtitle-source validation

Use this when the user explicitly says a lecture, keynote, speech, or oral presentation does not need visual analysis.

## Mode switch

- Treat the request as an explicit transcript-led run.
- Cancel Gemini visual analysis, frame extraction, GIF generation, and visual QA.
- Continue with transcript acquisition, metadata, theme map, deep-reading draft, fidelity check, Final Gate, and the requested publishing handoff.
- Do not make visual claims such as 「畫面顯示」「投影片上」「如圖」 unless independently verified. A speaker mentioning a slide in the transcript is still transcript evidence, not visual verification.
- Do not generate concept figures unless the user asks for article illustrations or the governing workflow explicitly requires them.

## Subtitle-source validation

A transcript helper can return a non-empty file and still choose an inferior source. YouTube rolling captions can also create repeated phrases that inflate line and character counts.

Before theme mapping:

1. Record video duration from metadata.
2. Prefer the canonical `video-to-article/scripts/get_transcript.py` output because it reports method, language, `is_generated`, segment count, duration coverage, paths, and quality badge.
3. Validate transcript coverage against video duration. Aim for at least 90%; below 80–90% is partial and must be repaired before writing.
4. Read a beginning, middle, and ending slice. Look for rolling-caption duplication where the same phrase appears two or three times in adjacent text.
5. If a convenience helper reports auto captions or produces heavy repetition, do not accept its manifest at face value. Rerun the canonical extractor with the source language explicitly selected. A later manual-caption result supersedes the earlier auto-caption file.
6. Replace the working transcript only after the cleaner source is verified, then build the theme map from that final file. If a subagent was dispatched against the bad transcript, rerun only the affected theme-map/draft task against the clean source.

## Reporting

Report the final transcript method, language, manual/auto status, segment count, coverage ratio, and the explicit no-visual mode. Do not expose internal pipeline caveats inside the public article; keep them in the work report or fidelity log.
