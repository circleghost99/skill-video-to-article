# Stable Preview Artifacts for v2a

## Why this exists

`video-to-article` often works inside macOS temp directories such as `/var/folders/.../openclaw-video-to-article/...`. Those paths are fine during extraction and drafting, but they are fragile for Discord preview and follow-up sessions. If the agent previews a Markdown file whose image links still point at `/var/folders/...`, later publishing or review may fail after cleanup or compaction.

## Standard pattern before preview

Before sending the draft or contact sheet to the user, persist the deliverables to a stable profile-owned directory:

```bash
python3 - <<'PY'
from pathlib import Path
import shutil

src = Path('/ABS/TEMP_DIR')
video_id = 'VIDEO_ID'
out = Path('/Users/circleghost/.hermes/profiles/hamster/outputs/v2a') / video_id
out.mkdir(parents=True, exist_ok=True)

for name in ['article_draft.md', 'contact_sheet.jpg', 'fidelity_check.md', 'notes_theme-map.md']:
    p = src / name
    if p.exists():
        shutil.copy2(p, out / name)

img_src = src / 'outputs/images'
img_out = out / 'images'
if img_src.exists():
    if img_out.exists():
        shutil.rmtree(img_out)
    shutil.copytree(img_src, img_out)

article = out / 'article_draft.md'
if article.exists():
    text = article.read_text(encoding='utf-8')
    text = text.replace(str(img_src), str(img_out))
    article.write_text(text, encoding='utf-8')

print('ARTICLE', out / 'article_draft.md')
print('CONTACT', out / 'contact_sheet.jpg')
print('IMAGES', img_out)
PY
```

Then rerun Final Gate against the stable article path:

```bash
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/final_gate.py \
  /Users/circleghost/.hermes/profiles/hamster/outputs/v2a/VIDEO_ID/article_draft.md --check-only
```

## Notes

- Keep working files in the temp directory until the user approves publishing.
- Use the stable copied `article_draft.md` for Discord preview attachments.
- Use stable copied image paths inside the article so later Notion upload can still find local images.
- Do not cleanup the temp directory until publishing/Obsidian sync is complete and user confirmation is no longer needed.
