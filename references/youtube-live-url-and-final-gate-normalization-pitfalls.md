# YouTube live URL + Final Gate normalization pitfalls

Session note from a transcript-led v2a run on a YouTube Live URL (`https://www.youtube.com/live/<id>?...`).

## 1. Normalize YouTube Live URLs before `video_analyzer.py`

`video_analyzer.py` accepts YouTube URLs, but a `/live/<id>?...` URL may be misinterpreted as a local path in some paths of the script and fail with a `Video file not found: .../https:/www.youtube.com/live/...` style error.

Durable pattern:

```bash
# Convert live URL to canonical watch URL before Step 02 / Step 04
URL="https://www.youtube.com/watch?v=VIDEO_ID"
```

If the user provides a `/live/VIDEO_ID` URL, extract `VIDEO_ID` and use `https://www.youtube.com/watch?v=VIDEO_ID` for:

- `scripts/video_analyzer.py`
- `scripts/get_transcript.py`
- `yt-dlp --dump-json` / subtitle checks

This is a normalization step, not a claim that YouTube Live sources are unsupported.

## 2. Final Gate can over-normalize some natural Taiwanese wording

`final_gate.py` runs zhtw / OpenCC normalization. It can occasionally convert ordinary wording in an awkward way, e.g. `只` → `隻` inside phrases like `不是只停在...` after normalization.

Recommended pattern:

1. Run `final_gate.py` normally so deterministic checks still happen.
2. Do a small post-gate sanity scan for likely over-normalization:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('/absolute/path/article_draft.md')
text = p.read_text(encoding='utf-8')
for bad in ['不是隻', '不隻', '只留下一串']:
    if bad in text:
        print('CHECK', bad)
PY
```

3. Patch only the awkward wording, then rerun `final_gate.py` again.

Do not skip Final Gate because of this. Treat it as a final human-language sanity pass after deterministic normalization.

## 3. Transcript-led no-image run still needs stable artifacts

When Gemini spending cap blocks visual analysis and Step 03 is cancelled, still copy the text artifacts into the stable profile output directory before preview:

- `article_draft.md`
- `fidelity_check.md`
- `notes_theme-map.md`
- `metadata.json`
- `transcript_clean.txt`

No `contact_sheet.jpg` is expected in this case. The final report should explicitly say the article is transcript-led and contains no verified video frames.
