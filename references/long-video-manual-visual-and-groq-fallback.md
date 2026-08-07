# Long-video manual visual + Groq fallback

## When to use

Use this degraded path when a long YouTube video has no retrievable captions and Gemini video upload is blocked by a project/provider spending cap, but the original video was downloaded successfully.

This is a recovery workflow, not proof that the normal Gemini analyzer completed.

## Evidence-preserving sequence

1. **Keep the original source**
   - Reuse the analyzer's local `video_source.mp4`.
   - Save the exact provider error in the run notes.
   - Mark `analysis.json` with a fallback mode and preserve `metadata.local_video_path`.

2. **Chunk ASR before calling Groq**
   - Extract mono audio at 16 kHz and a low bitrate, for example 24 kbps MP3.
   - Split by duration into bounded chunks (8 minutes was safe in the observed run), rather than sending a 1–2 hour file in one request.
   - Transcribe each chunk with an explicit language, then concatenate in filename order.
   - Treat the result as noisy source material: preserve uncertainty and do not promote suspicious ASR names, amounts, or product claims to facts without another source.

3. **Coarse visual sweep**
   - Use ffmpeg to sample at a wide interval such as one frame per 120 seconds and tile frames into contact sheets.
   - Ask vision to identify only non-talking-head regions: slides, dashboards, forms, diagrams, charts, product UIs, and completed states.
   - Narrow the interval to one frame per 60 seconds across candidate spans when the coarse sweep shows useful screen-share content.

4. **Timestamp extraction**
   - Convert contact-sheet cell positions back to timestamps.
   - Extract full-resolution JPEGs from the original video with ffmpeg at those timestamps.
   - Create a manifest containing absolute file paths, timestamp seconds, description, importance, and article context.

5. **Second visual QA gate**
   - Build a final contact sheet from the candidate frames and run vision again.
   - Remove frames that are loading/empty states, repeated views, heavily obstructed screens, or mostly talking head.
   - If tiny text is not legible in the contact sheet, describe only the visible page type or large heading. Do not assert exact small numbers or labels.
   - Keep a rejected-frame list for auditability.

## Public-article wording rules

- Say “畫面可見” only for topics confirmed by the final contact-sheet QA.
- Keep transcript-derived claims separate from visually observed claims.
- Disclose the degraded source quality in internal run notes and `quality_badge`; do not invent a normal Gemini-success badge.
- Do not publish provider errors, internal temp paths, or speculative OCR as if they were part of the source.

## Common mistakes

- Retrying the same provider after a spending-cap error instead of switching to a transparent fallback.
- Sending the whole long audio file to Groq and hitting the entity-size limit.
- Treating a low-resolution vision guess as exact text transcription.
- Keeping every minute-by-minute duplicate frame instead of selecting topic representatives.
- Calling the fallback “Gemini visual analysis completed.”
