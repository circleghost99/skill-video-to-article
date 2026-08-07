# Gemini visual proxy analysis fallback

Use this when full-resolution video upload succeeds or starts, but Gemini File API server-side processing stalls / times out, or the video is too large for reliable visual analysis. This is not a reason to abandon visual QA if the user still wants screenshots.

## Pattern

1. Keep the original high-resolution video path. This remains the source for final screenshots / GIFs.
2. Create a lightweight visual proxy for Gemini:

```bash
/opt/homebrew/bin/ffmpeg -y \
  -i /abs/path/original.mp4 \
  -an -vf "fps=1,scale=-2:360" \
  -c:v libx264 -preset veryfast -crf 32 \
  /abs/workdir/video_visual_1fps_360p.mp4
```

3. Run `video_analyzer.py` on the proxy, not the original:

```bash
set -a; source /Users/circleghost/.hermes/profiles/hamster/.env; set +a
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/video_analyzer.py \
  /abs/workdir/video_visual_1fps_360p.mp4 \
  -o analysis.json --keep-file --model gemini-2.5-flash
```

4. Treat the proxy timestamps as the same timeline as the original, because fps/scale changes do not alter duration. Use the original video for asset extraction so screenshots remain high quality.
5. Before extraction, optionally filter `analysis.json` down to high-value evidence frames that match the article thesis. Remove b-roll, city shots, office decor, childhood photos, pure personality shots, and weak concept art unless the article needs them.
6. If the canonical `extract_assets.sh` fails because its micro-aligner cannot run, do not stop. Extract selected frames directly with ffmpeg from the original video and write a compatible manifest:

```bash
/opt/homebrew/bin/ffmpeg -y -ss <seconds> -i /abs/path/original.mp4 \
  -vframes 1 -q:v 2 -update 1 /abs/workdir/images/images/frame_NN_MM_SS.jpg \
  -loglevel error
```

7. Build an all-frame contact sheet for QA. The built-in `create_contact_sheet.py` may only show the first four images; for >4 images, create a simple PIL grid or another full-sheet preview.
8. Run vision QA on the full contact sheet. Only insert frames that are non-empty, not pure talking heads, legible enough, and directly tied to a paragraph.
9. Copy final images and article to the stable profile output directory, rewrite image paths to the stable directory, then rerun Final Gate and a lightweight check for missing image paths / consecutive images.

## Why this works

Gemini needs only enough visual resolution to identify candidate moments and timestamps. The article needs high-quality evidence frames. Splitting those roles lets the pipeline recover from large-video Gemini processing timeouts without lowering final image quality.

## Guardrails

- Be explicit in the user-facing report: visual analysis used a downsampled proxy, final screenshots came from the original high-resolution video.
- Do not use proxy screenshots in the article unless the original video is unavailable.
- Do not claim a frame is verified until contact sheet / vision QA has checked the actual extracted images.
- Do not keep weak screenshots just to satisfy a quota; fewer relevant evidence frames are better than many b-roll images.
