# Local MP4 transcript-led ASR fallback

Use this when v2a is given a local MP4 file and visual analysis is blocked or unavailable, but the user still wants a deep reading article.

## Trigger

- Source is a local video path, not a YouTube URL.
- Gemini visual analysis fails with a spending-cap / File API blocker, or visual work is explicitly deferred.
- No YouTube caption path exists, but the audio is usable.

## Workflow

1. Mark Step 02 visual analysis and Step 03 asset extraction as blocked/cancelled with the exact blocker. Do not invent screenshots or visual claims.
2. Extract compressed speech audio from the local video:

```bash
/opt/homebrew/bin/ffmpeg -y \
  -i "/absolute/path/video.mp4" \
  -vn -ac 1 -ar 16000 -b:a 32k \
  "$WORK/audio_16k_mono.mp3" \
  -loglevel error
```

3. Transcribe with `groq-transcriber` when available. For English interviews, force English to avoid mixed Chinese hallucination / mistranscription:

```bash
python3 /Users/circleghost/.hermes/profiles/hamster/skills-imports/groq-transcriber/scripts/transcribe.py \
  "$WORK/audio_16k_mono.mp3" \
  --language en \
  > "$WORK/transcript_en_raw.txt"
```

4. Clean and chunk the transcript into `transcript_clean.txt`. Normalize obvious ASR product-name errors before writing theme maps, especially:
   - `CloudCode`, `Cloud Code`, `QuadCode`, `Quad Code`, `quad code` → `Claude Code`
   - lowercase / partial variants only when context clearly refers to Claude Code or Claude.
5. Write a small `metadata.json` with source path, duration, transcript method, quality badge, and visual blocker. Use it instead of `analysis.json` for Step 05/06 when visual analysis never produced JSON.
6. Continue with normal transcript-led v2a: theme map → draft → editorial review with no images → fidelity check → Final Gate → stable preview artifacts.

## Guardrails

- Public article intro should not say “this was based on ASR” or narrate pipeline state. Put that in work report / quality log. Keep `quality_badge` in frontmatter for transparency.
- No Markdown images, frame/gif placeholders, or phrases like `畫面顯示`, `投影片上`, `如圖`, `截圖`, `我看到畫面` unless a later visual pass verifies them.
- After `final_gate.py`, re-check user terminology. The converter may turn preferred `智能體` into banned `智慧體`, or create zh-en spacing issues around `Agent`. Fix terminology/spacing, then rerun Final Gate or a lightweight gate.
- If final output uses `Agent`, enforce spaces around it in Chinese text: `讓 Agent`, `Agent 工作流`, not `讓Agent`.

## Why this matters

A local MP4 has no caption API path, but it can still produce a responsible deep-reading article through ASR. The key is transparent downgrade plus strict no-visual-claim hygiene.