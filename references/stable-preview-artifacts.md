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

## Contact sheet pitfall

`create_contact_sheet.py` may warn `More than 4 images provided, only using the first 4`. For V2A preview this is easy to miss: the contact sheet can look valid while silently omitting later inserted evidence frames / GIFs. If the article uses more than four media assets, create a custom PIL contact sheet (2 columns × N rows is fine) that includes every inserted frame/GIF first frame, then copy that `contact_sheet.jpg` to the stable output directory. The preview should represent the actual media set in the article, not just the first four files.

## Dense-slide QA pitfall: contact sheets can hide blocking overlays

A contact sheet is sufficient for broad filtering, but its reduced cells can conceal macOS permission dialogs, update prompts, browser popovers, or other overlays on chart-heavy slides. A frame may look usable in the sheet while a full-resolution read shows that the benchmark or chart is partially blocked.

For every retained dense chart, benchmark, UI, or text-heavy slide:

1. Inspect the full-resolution frame separately after the broad contact-sheet pass.
2. If an overlay or cursor blocks important content, extract candidates at `-2s`, `-1s`, `+1s`, and `+2s` (or a slightly wider range when the overlay persists).
3. Compare the candidates in one small sheet, replace the original with the cleanest frame, and update the timestamp in every manifest copy.
4. Rebuild the final contact sheet after replacement and have the main agent visually confirm the corrected frame. A subagent summary alone is not enough for the final visual gate.

## Final preview contact sheet must match the article's actual media set

The preview sheet should contain exactly the frames used by `article_draft.md`, plus the first frame of each retained GIF. Do not preview all extracted assets when the article uses only a subset, and do not omit GIFs.

Two common shortcuts are unreliable for more than four assets:

- `create_contact_sheet.py` explicitly keeps only the first four inputs.
- A single image-sequence input combined with FFmpeg `tile` may emit only the first row even when the canvas is larger; a valid-looking output can therefore contain four images and blank cells.

For a final sheet with more than four media items, use FFmpeg with one explicit `-i` per image and `xstack=inputs=N:layout=...`. First extract each GIF's first frame to a QA directory. Scale every input to the same dimensions, build a `4 + 4 + remainder` layout, then visually verify that the expected number of non-empty cells is present. If vision reports only the first four cells, treat the sheet as failed and rebuild it rather than accepting the file's dimensions as proof.

## Post-Final-Gate language sweep

After the full Final Gate writes normalization changes, scan the stable article for known over-normalizations such as `許可權`, `隻能`, `聯結器`, `智慧體`, and `程式記憶`. Repair them to natural Taiwan usage (`權限`, `只能`, `連接器`, `智能體`, `程序記憶` as context requires), then run only the lightweight non-mutating checks: image existence, continuous-image detection, HTML tags, U+2014/U+2015, body dividers, double commas, risky corruption characters, and cover preservation. Do not rerun the mutating normalizer after manually restoring wording, or it may reintroduce the same drift.

## Notes

- Keep working files in the temp directory until the user approves publishing.
- Use the stable copied `article_draft.md` for Discord preview attachments.
- Use stable copied image paths inside the article so later Notion upload can still find local images.
- Do not cleanup the temp directory until publishing/Obsidian sync is complete and user confirmation is no longer needed.
