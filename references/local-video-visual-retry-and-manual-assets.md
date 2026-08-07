# Local video visual retry + manual asset extraction notes

Session pattern captured from a local-file v2a run where the first Gemini attempt hit spending cap, the user raised the cap, and the visual pass was resumed after a transcript-led draft already existed.

## When this applies

Use this note when:
- the source is a local `.mp4`, not a YouTube URL;
- Step 02 was previously blocked by Gemini quota/spending cap, then the user fixes quota and asks to resume visual analysis;
- `video_analyzer.py` or `extract_assets.sh` cannot complete the normal path, but `analysis.json` contains usable timestamps.

## Resume pattern after quota is fixed

1. Keep the existing transcript-led artifacts (`article_draft.md`, `transcript_clean.txt`, `notes_theme-map.md`, `fidelity_check.md`). Do not restart writing from scratch.
2. Rerun Step 02 with the local video path and `--keep-file`:

```bash
/opt/homebrew/bin/python3 /path/to/video_analyzer.py \
  "/absolute/path/source.mp4" \
  -o analysis.json \
  --strip-audio \
  --keep-file \
  --model gemini-2.5-flash
```

3. If the default Python cannot import `google.genai`, try the Homebrew Python that has the SDK installed instead of rewriting the workflow. If env vars are not inherited, load the existing Hermes env in a shell before the command. Treat this as a Python/environment selection fix, not as a reason to abandon visual analysis.
4. Read back `analysis.json` before extracting assets. For local videos, compare `metadata.video_duration_seconds` with `analysis.video_info.duration_seconds`; if the model only focused on a shorter demo segment, be explicit that the visual assets cover that segment, not necessarily the whole interview.

## Manual ffmpeg extraction fallback

If `extract_assets.sh` exits early but `analysis.json` has valid `key_frames` / `gif_segments`, do not block the visual pass. Extract directly from the original high-resolution video and write a compatible `manifest.json`.

Minimal pattern:

```python
from pathlib import Path
import json, subprocess

work = Path('/ABS/WORKDIR')
video = Path('/ABS/SOURCE.mp4')
out = work / 'outputs' / 'images'
out.mkdir(parents=True, exist_ok=True)
data = json.load(open(work / 'analysis.json'))

def ts_to_sec(ts):
    p = [int(x) for x in ts.split(':')]
    return p[0]*60 + p[1] if len(p) == 2 else p[0]*3600 + p[1]*60 + p[2]

def slug(ts):
    return ts.replace(':', '_')

assets = []
for i, k in enumerate(data['analysis'].get('key_frames', []), 1):
    ts = k['timestamp']
    fn = f'frame_{i:02d}_{slug(ts)}.jpg'
    path = out / fn
    subprocess.run([
        '/opt/homebrew/bin/ffmpeg', '-y', '-ss', str(ts_to_sec(ts)),
        '-i', str(video), '-vframes', '1', '-q:v', '2', str(path),
        '-loglevel', 'error'
    ], check=True)
    assets.append({**k, 'asset_type': 'frame', 'file': str(path), 'path': str(path), 'filename': fn})

for i, g in enumerate(data['analysis'].get('gif_segments', []), 1):
    st, en = g['start_time'], g['end_time']
    dur = max(1, min(12, ts_to_sec(en) - ts_to_sec(st)))
    fn = f'gif_{i:02d}_{slug(st)}-{slug(en)}.gif'
    path = out / fn
    subprocess.run([
        '/opt/homebrew/bin/ffmpeg', '-y', '-ss', str(ts_to_sec(st)), '-t', str(dur),
        '-i', str(video), '-vf', 'fps=8,scale=960:-1:flags=lanczos',
        '-loop', '0', str(path), '-loglevel', 'error'
    ], check=True)
    assets.append({**g, 'asset_type': 'gif', 'file': str(path), 'path': str(path), 'filename': fn})

manifest = {
    'source_video': str(video),
    'analysis_path': str(work / 'analysis.json'),
    'output_dir': str(out),
    'assets': assets,
    'key_frames': [a for a in assets if a['asset_type'] == 'frame'],
    'gif_segments': [a for a in assets if a['asset_type'] == 'gif'],
}
(work / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
```

## Contact sheet QA pitfall

`create_contact_sheet.py` may cap output to the first 4 images. If there are more than 4 frames, either generate multiple sheets or build a simple PIL grid so every candidate appears in the QA artifact. Do not claim "all screenshots reviewed" if the contact sheet only contains the first four.

After manual extraction, still perform the normal QA gates:
- frame contact sheet: no empty/black/talking-head-only frames, text is readable;
- GIF first/last contact sheet: no black/blank/pure transition frames;
- article insertion check: no consecutive images, paths are absolute, Final Gate passes after the last image insertion;
- stable preview copy: copy `analysis.json`, `manifest.json`, `contact_sheet.jpg`, `gif_contact_sheet.jpg`, `article_draft.md`, and `outputs/images/` into the stable profile output directory before handoff.
