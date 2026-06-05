# v2a: video analyzer readback and vision-provider fallback

Origin: Discord session `20260526_190051_52c5116a` involved an X embedded workshop video. `vision_analyze` failed because its configured Gemini model was removed, but `scripts/video_analyzer.py --model gemini-2.5-flash` succeeded.

## Durable rule

After `video_analyzer.py` completes, do not rely on the long terminal log as the only evidence. Read back the generated `analysis.json` and extract the small set of fields needed by downstream writing:

- `analysis.content_summary`
- `analysis.video_info`
- high/medium `analysis.key_frames[]` with timestamp, description, and visible text if present
- `analysis.gif_segments[]` when relevant
- `metadata.local_video_path`, `metadata.youtube_thumbnail_url`, and token/cost metadata

This protects against terminal output truncation and prevents the writer from making claims from partially visible logs.

## Provider/model 404 handling

If any auxiliary vision tool fails with a provider/model 404 such as:

```text
Gemini HTTP 404 (NOT_FOUND): This model models/gemini-3.1-flash-lite-preview is no longer available
```

Do not retry the same tool or sleep. Treat it as provider configuration drift. Use one of:

1. `video_analyzer.py --model gemini-2.5-flash` for whole-video analysis;
2. local OCR / macOS Vision / PIL metadata when checking individual frames;
3. a provider health/config fix outside the article workflow.

## Writing handoff implication

When the session is an embedded X video plus thread/article context, split work before writing:

- source map: tweet claim, transcript outline, visual observations, referenced-thread claims;
- interpretation map: what is observed vs what is the agent's analysis;
- final writing: main agent or a smaller delegate task focused only on style.

Avoid one oversized delegate prompt that asks a child agent to read every source, synthesize architecture, write the full article, and enforce style at once; it can time out after several API calls without returning useful text.
