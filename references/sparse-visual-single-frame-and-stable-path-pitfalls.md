# Sparse visual / single-frame v2a pitfalls

Session-derived notes from a YouTube companion podcast with almost no useful visuals.

## When Gemini returns only one valid frame

If `analysis.json` contains only one useful `key_frame` and no GIFs, do not force the normal「至少 3 張配圖」heuristic. The correct outcome is:

1. Extract and visually verify the single frame.
2. Write a compatible `manifest.json` with that one verified image.
3. In Step 07, explicitly tell the reviewer subagent that the one-frame manifest is intentional and that it must not invent, duplicate, or insert low-value talking-head frames to satisfy the 3-image default.
4. In the final report, say that the video is visually sparse and the article is transcript-led with one evidence frame.

This is different from a failed visual pass. The visual pass succeeded, but the source video did not contain multiple evidence-worthy frames.

## Manual ffmpeg fallback after extractor failure

If `extract_assets.sh` exits early after printing the first frame line, but `analysis.json` has a valid timestamp and `video_source.mp4` exists, use a deterministic direct extraction instead of blocking:

```bash
mkdir -p outputs/images
ffmpeg -y -ss 00:00:05 -i video_source.mp4 -vframes 1 -q:v 2 outputs/images/frame_01_00_05.jpg -loglevel error
```

Then write a minimal manifest compatible with Step 07:

```json
{
  "assets": [{"type": "image", "path": "/ABS/PATH/outputs/images/frame_01_00_05.jpg", "timestamp": "00:05", "description": "...", "article_context": "..."}],
  "images": [{"path": "/ABS/PATH/outputs/images/frame_01_00_05.jpg", "timestamp": "00:05", "description": "...", "article_context": "..."}],
  "gifs": []
}
```

A manual fallback still requires vision QA. Verify the frame is a real, readable screenshot, not an empty frame, black screen, or pure talking head.

## Stable-copy path normalization pitfall

macOS temp paths often have both `/var/folders/...` and `/private/var/folders/...` spellings. When stable-copying images into `/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/<VIDEO_ID>/images`, replace the `/private`-prefixed source path before or in addition to the non-prefixed source path.

Bad replacement order can produce broken paths like:

```text
/private/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/<VIDEO_ID>/images/frame.jpg
```

After stable-copy and before final response, always parse Markdown image links and assert every local image path exists.

```python
from pathlib import Path
import re
article = Path('/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/VIDEO_ID/article_draft.md')
text = article.read_text()
imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
assert all(Path(p).exists() for p in imgs if not p.startswith('http')), imgs
```

## Final Gate over-normalization sweep

After `final_gate.py`, do a quick phrase sweep for common over-normalizations before delivery, especially in technical articles:

- `許可權` → usually should be `權限`
- `不是隻` → usually should be `不是只`
- `對映` → often should be `對應`
- `改進物件` / `批判物件` → usually should be `改進對象` / `批判對象`

If you manually fix these after Final Gate, rerun the lightweight checks: HTML tag count, em dash absence, body divider positions, continuous images, and local image path existence.