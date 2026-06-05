#!/usr/bin/env python3
"""get_transcript.py — Single-entry transcript fetcher with priority chain.

Priority order (each step only runs if the previous yielded nothing):
  1. youtube-transcript-api  — fastest, no rate-limit risk
  2. yt-dlp --write-subs --write-auto-subs  — covers cases the API misses,
                                              with 429 backoff
  3. mlx-whisper large-v3  — local ASR fallback, only when YT has no subs
                             at all (requires --audio)

Outputs (in --out-dir):
  transcript_raw.json   — list of {start, duration, text}
  transcript_clean.txt  — chunked plain text with [MM:SS] markers

Stdout: JSON status report. Caller (agent) parses this to write
frontmatter quality_badge etc.

Usage:
  python3 get_transcript.py --url <YT_URL> --out-dir <DIR> \\
      [--audio <PATH>] [--lang zh] [--skip-whisper]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Target language → ranked list of YouTube language codes (best first).
LANG_PREFS: dict[str, list[str]] = {
    "zh": ["zh-TW", "zh-Hant", "zh-CN", "zh-Hans", "zh", "zh-HK"],
    "en": ["en", "en-US", "en-GB"],
}

# Comma-separated --sub-langs argument for yt-dlp.
YTDLP_LANG_CODES: dict[str, str] = {
    "zh": "zh-Hant,zh-TW,zh-Hans,zh-CN,zh,zh-HK,zh-Hant-zh,zh-Hans-zh,en",
    "en": "en,en-US,en-GB,en-zh",
}


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/").split("/")[0]
    if "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        m = re.match(r"^/(?:embed|shorts|live)/([\w-]+)", parsed.path)
        if m:
            return m.group(1)
    raise ValueError(f"Cannot extract video ID from URL: {url}")


# ── Method 1: youtube-transcript-api ─────────────────────────────────
def try_youtube_transcript_api(video_id: str, lang: str) -> dict:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return {"ok": False, "reason": "youtube-transcript-api not installed"}

    pref_codes = LANG_PREFS.get(lang, [lang])

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
    except Exception as e:
        return {"ok": False, "reason": f"list failed: {type(e).__name__}: {e}"}

    candidates = list(transcript_list)
    if not candidates:
        return {"ok": False, "reason": "no transcripts available"}

    def rank(t) -> tuple:
        manual = 0 if not t.is_generated else 1
        try:
            lang_idx = pref_codes.index(t.language_code)
        except ValueError:
            lang_idx = 999
        return (manual, lang_idx)

    candidates.sort(key=rank)
    chosen = candidates[0]

    try:
        fetched = chosen.fetch()
    except Exception as e:
        return {"ok": False, "reason": f"fetch failed: {type(e).__name__}: {e}"}

    segments = [
        {"start": float(s.start), "duration": float(s.duration), "text": s.text}
        for s in fetched
    ]
    return {
        "ok": True,
        "method": "youtube-transcript-api",
        "language": chosen.language_code,
        "is_generated": chosen.is_generated,
        "segments": segments,
    }


# ── Method 2: yt-dlp ─────────────────────────────────────────────────
def _run_yt_dlp(url: str, out_dir: Path, sub_langs: str, auto: bool) -> dict:
    """Single yt-dlp invocation with 429 backoff. Returns {ok, vtts, reason}."""
    pattern = out_dir / ("yt_auto_subs.%(ext)s" if auto else "yt_subs.%(ext)s")
    glob_pattern = "yt_auto_subs*.vtt" if auto else "yt_subs*.vtt"

    flags = ["--write-subs"]
    if auto:
        flags.append("--write-auto-subs")

    last_err = ""
    for delay in (0, 5, 15):
        if delay:
            time.sleep(delay)
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    *flags,
                    "--sub-langs",
                    sub_langs,
                    "--sub-format",
                    "vtt",
                    "--skip-download",
                    "-o",
                    str(pattern),
                    url,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            vtts = sorted(out_dir.glob(glob_pattern))
            return {"ok": True, "vtts": vtts}
        except subprocess.CalledProcessError as e:
            last_err = (e.stderr or e.stdout or "").strip()
            if "429" not in last_err and "Too Many Requests" not in last_err:
                return {"ok": False, "reason": f"yt-dlp error: {last_err[:300]}"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "reason": "yt-dlp timeout"}
    return {"ok": False, "reason": f"yt-dlp 429 after retries: {last_err[:200]}"}


def try_yt_dlp(url: str, out_dir: Path, lang: str) -> dict:
    if not shutil.which("yt-dlp"):
        return {"ok": False, "reason": "yt-dlp not on PATH"}

    sub_langs = YTDLP_LANG_CODES.get(lang, lang)

    # Manual subs first (better quality)
    res = _run_yt_dlp(url, out_dir, sub_langs, auto=False)
    is_generated = False
    if not (res["ok"] and res.get("vtts")):
        # No manual subs found → try auto-captions
        res = _run_yt_dlp(url, out_dir, sub_langs, auto=True)
        is_generated = True

    if not (res["ok"] and res.get("vtts")):
        return {"ok": False, "reason": res.get("reason", "no vtt files downloaded")}

    pref_codes = LANG_PREFS.get(lang, [lang])

    def vtt_rank(p: Path) -> int:
        m = re.search(r"\.([A-Za-z\-]+)\.vtt$", p.name)
        code = m.group(1) if m else ""
        try:
            return pref_codes.index(code)
        except ValueError:
            return 999

    vtts = sorted(res["vtts"], key=vtt_rank)
    chosen = vtts[0]
    segments = parse_vtt(chosen.read_text(encoding="utf-8"))
    if not segments:
        return {"ok": False, "reason": f"vtt parsed to 0 segments: {chosen.name}"}

    code_match = re.search(r"\.([A-Za-z\-]+)\.vtt$", chosen.name)
    return {
        "ok": True,
        "method": "yt-dlp",
        "language": code_match.group(1) if code_match else "unknown",
        "is_generated": is_generated,
        "segments": segments,
        "vtt_file": chosen.name,
    }


def parse_vtt(vtt_text: str) -> list[dict]:
    """Parse WebVTT cues. Strips inline timestamps + dedupes rolling auto-caption text."""
    segments: list[dict] = []
    last_text = ""
    for block in re.split(r"\n\n+", vtt_text):
        lines = block.strip().split("\n")
        ts_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if ts_idx is None:
            continue
        m = re.match(
            r"(\d+):(\d+):(\d+)[\.,](\d+)\s+-->\s+(\d+):(\d+):(\d+)[\.,](\d+)",
            lines[ts_idx],
        )
        if not m:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(x) for x in m.groups())
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        text = "\n".join(lines[ts_idx + 1 :])
        text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        # YouTube auto-captions repeat the previous cue's text as a prefix; trim it.
        if last_text and text.startswith(last_text):
            text = text[len(last_text):].strip()
        if not text:
            continue
        segments.append({"start": start, "duration": end - start, "text": text})
        last_text = segments[-1]["text"]
    return segments


# ── Method 3: mlx-whisper fallback ───────────────────────────────────
def try_mlx_whisper(audio: Path, lang: str) -> dict:
    try:
        import mlx_whisper
    except ImportError:
        return {
            "ok": False,
            "reason": (
                "mlx-whisper not installed. Install with: "
                "`pip install mlx-whisper` (Apple Silicon only)."
            ),
        }

    if not audio.exists():
        return {"ok": False, "reason": f"audio file not found: {audio}"}

    initial_prompt = "以下是繁體中文逐字稿。" if lang == "zh" else None

    try:
        result = mlx_whisper.transcribe(
            str(audio),
            path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
            language=lang,
            initial_prompt=initial_prompt,
            condition_on_previous_text=True,
            verbose=False,
        )
    except Exception as e:
        return {"ok": False, "reason": f"mlx-whisper failed: {type(e).__name__}: {e}"}

    segments = [
        {
            "start": float(s["start"]),
            "duration": float(s["end"] - s["start"]),
            "text": s["text"].strip(),
        }
        for s in result.get("segments", [])
        if s.get("text", "").strip()
    ]
    if not segments:
        return {"ok": False, "reason": "mlx-whisper produced 0 segments"}

    return {
        "ok": True,
        "method": "mlx-whisper",
        "model": "large-v3",
        "language": result.get("language", lang),
        "is_generated": True,
        "segments": segments,
    }


# ── Output writers ───────────────────────────────────────────────────
def write_outputs(segments: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "transcript_raw.json"
    clean_path = out_dir / "transcript_clean.txt"
    raw_path.write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    clean_path.write_text(clean_segments(segments), encoding="utf-8")
    return raw_path, clean_path


def clean_segments(segments: list[dict], chunk_sec: float = 30.0) -> str:
    """Group segments into ~chunk_sec windows; each chunk prefixed with [MM:SS]."""
    if not segments:
        return ""
    out: list[str] = []
    buf: list[str] = []
    chunk_start = segments[0]["start"]
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        if seg["start"] - chunk_start >= chunk_sec and buf:
            out.append(_fmt_chunk(chunk_start, " ".join(buf)))
            buf = []
            chunk_start = seg["start"]
        buf.append(text)
    if buf:
        out.append(_fmt_chunk(chunk_start, " ".join(buf)))
    return "\n\n".join(out) + "\n"


def _fmt_chunk(start_sec: float, text: str) -> str:
    mm, ss = divmod(int(start_sec), 60)
    text = re.sub(r"\s+", " ", text).strip()
    return f"[{mm:02d}:{ss:02d}] {text}"


def quality_badge(method: str, is_generated: bool) -> str:
    if method == "mlx-whisper":
        return "🟡 本地 ASR 轉錄 (whisper large-v3)"
    if is_generated:
        return "🟡 自動字幕"
    return "🟢 人工字幕"


# ── Main ─────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--url", required=True, help="YouTube URL")
    p.add_argument("--out-dir", required=True, help="Output directory")
    p.add_argument("--audio", help="Audio file (only used for whisper fallback)")
    p.add_argument("--lang", default="zh", help="Target language (default: zh)")
    p.add_argument(
        "--skip-whisper",
        action="store_true",
        help="Don't fall back to whisper even when subs unavailable",
    )
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    audio = Path(args.audio) if args.audio else None

    try:
        video_id = extract_video_id(args.url)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(2)

    attempts: list[dict] = []

    print("→ trying youtube-transcript-api...", file=sys.stderr)
    result = try_youtube_transcript_api(video_id, args.lang)
    if not result["ok"]:
        attempts.append({"method": "youtube-transcript-api", "reason": result["reason"]})
        print(f"  failed: {result['reason']}", file=sys.stderr)
        print("→ trying yt-dlp...", file=sys.stderr)
        result = try_yt_dlp(args.url, out_dir, args.lang)
    if not result["ok"]:
        attempts.append({"method": "yt-dlp", "reason": result["reason"]})
        print(f"  failed: {result['reason']}", file=sys.stderr)
        if args.skip_whisper:
            print(json.dumps(
                {"ok": False, "error": "no YT subs and --skip-whisper set",
                 "attempts": attempts},
                ensure_ascii=False, indent=2,
            ))
            sys.exit(3)
        if not audio:
            print(json.dumps(
                {"ok": False, "error": "YT subs unavailable and --audio not given",
                 "attempts": attempts},
                ensure_ascii=False, indent=2,
            ))
            sys.exit(3)
        print("→ falling back to mlx-whisper...", file=sys.stderr)
        result = try_mlx_whisper(audio, args.lang)
    if not result["ok"]:
        attempts.append({"method": "mlx-whisper", "reason": result["reason"]})
        print(json.dumps(
            {"ok": False, "error": "all methods failed", "attempts": attempts},
            ensure_ascii=False, indent=2,
        ))
        sys.exit(4)

    raw_path, clean_path = write_outputs(result["segments"], out_dir)
    last = result["segments"][-1]
    duration = last["start"] + last["duration"]

    status = {
        "ok": True,
        "method": result["method"],
        "language": result.get("language"),
        "is_generated": result.get("is_generated"),
        "segments": len(result["segments"]),
        "duration_sec": round(duration, 2),
        "raw_path": str(raw_path),
        "clean_path": str(clean_path),
        "quality_badge": quality_badge(result["method"], result.get("is_generated", True)),
    }
    if result.get("model"):
        status["model"] = result["model"]
    if result.get("vtt_file"):
        status["vtt_file"] = result["vtt_file"]
    if attempts:
        status["fallback_from"] = attempts

    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
