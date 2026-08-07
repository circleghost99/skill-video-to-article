# X Embedded Video v2a Notes

Use this when the user gives an `x.com/.../status/...` URL and asks for v2a / deep video interpretation.

## Source acquisition

1. Convert the X status first with `baoyu-danger-x-to-markdown` and media download:

```bash
bun ~/.hermes/skills/openclaw-imports/baoyu-danger-x-to-markdown/scripts/main.ts \
  "https://x.com/<user>/status/<id>" \
  -o "$WORK/x-source/tweet.md" \
  --download-media
```

2. Treat the downloaded `x-source/videos/*.mp4` as the video source for `video_analyzer.py` and asset extraction.
3. Read `x-source/tweet.md` as context, not as the video transcript. If the X post contains a long article or reconstruction, label those claims as X-context / public-source reconstruction, not as facts the clip directly said or showed.

## Transcript path

X videos normally do not have YouTube captions. Use ASR:

```bash
ffmpeg -y -i "$VIDEO" -vn -ac 1 -ar 16000 -b:a 64k "$WORK/audio_16k_mono.mp3" -loglevel error
python3 ~/.hermes/profiles/hamster/skills-imports/groq-transcriber/scripts/transcribe.py \
  "$WORK/audio_16k_mono.mp3" --language en --timeout 300 > "$WORK/transcript_raw.txt"
```

Then clean / chunk into `transcript_clean.txt`. In frontmatter, mark a transparent `quality_badge`, e.g. `🟡 Groq Whisper ASR + X 長文補充`, and include a `source_note` that the ASR transcript is the primary video source while the X post is supplemental.

## Visual analysis and assets

- Run Gemini visual analysis against the local MP4, not the X URL.
- If the clip is mostly a talk / panel and Gemini returns only one useful event-wide frame, that is acceptable. Do not force 3+ screenshots when the video has no slides, UI, charts, or screen recordings.
- If `extract_assets.sh` exits because `frame_aligner.py` lacks OpenCV, use the existing fallback in `references/fallbacks.md`: directly extract the Gemini timestamp from the original video with ffmpeg, hand-write compatible `manifest.json`, then make a contact sheet and run vision QA.

Example direct extraction:

```bash
mkdir -p "$WORK/images/images"
ffmpeg -ss 16 -i "$VIDEO" -vframes 1 -q:v 2 -update 1 \
  "$WORK/images/images/frame_01_00_16.jpg" -y -loglevel error
```

## Writing boundary

The article must clearly separate:

- **影片直接證據**: claims present in ASR transcript or verified visual frame.
- **X 長文延伸重建**: analysis, architecture, file layouts, routines, or framework claims from the tweet/article.

Do not write X-thread details as if they were shown in the video. A good caveat sentence is:

> 本文的主證據來自影片 ASR 逐字稿；X 長文是公開資料延伸重建，不是影片逐字展示的私人設定。

## Stable preview artifact gotcha

Manual asset fallback may produce images under `$WORK/images/images`, not `$WORK/outputs/images`. Before preview, copy that directory into the stable v2a output folder and rewrite article image paths accordingly. Then rerun `final_gate.py` on the stable article path.
