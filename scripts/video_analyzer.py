#!/usr/bin/env python3
"""
video_analyzer.py — Gemini Video Analysis Script

Uploads a local video file (or passes a YouTube URL) to Gemini,
analyzes it for key frames and GIF-worthy segments, and outputs
structured JSON for downstream ffmpeg extraction.

Usage:
    python3 video_analyzer.py <video_path_or_youtube_url> [options]

Examples:
    # Local file
    python3 video_analyzer.py /path/to/video.mp4 -o analysis.json

    # YouTube URL
    python3 video_analyzer.py "https://www.youtube.com/watch?v=VIDEO_ID" -o analysis.json

    # With custom prompt addition
    python3 video_analyzer.py video.mp4 -o analysis.json --extra-prompt "特別注意 UI 操作畫面"

Requirements:
    pip install google-genai
    Environment variable: GEMINI_API_KEY
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("video_analyzer")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "gemini-3-flash-preview"

# Pricing per 1M tokens (USD) — Gemini 3 Flash Preview (as of 2026-04)
# https://ai.google.dev/gemini-api/docs/pricing
PRICE_INPUT_PER_M = 0.15   # $0.15 per 1M input tokens
PRICE_OUTPUT_PER_M = 0.60  # $0.60 per 1M output tokens

# Token estimation: ~300 tokens/second at default resolution
TOKENS_PER_SECOND_DEFAULT = 300
TOKENS_PER_SECOND_LOW = 100

YOUTUBE_URL_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
    r"(?:https?://)?youtu\.be/[\w-]+",
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+",
]

# ---------------------------------------------------------------------------
# Analysis prompt
# ---------------------------------------------------------------------------
ANALYSIS_PROMPT = """\
你是頂級的影片視覺分析專家與簡報/教學文獻整理師。
你的任務是「只看畫面」來分析這部影片，找出「所有」值得截圖或製成 GIF 的關鍵畫面。
數量不限，請盡可能詳盡，寧多勿少。

請以純 JSON 格式回傳，結構如下：

{
  "video_info": {
    "duration_seconds": <影片總秒數>,
    "content_type": "<talking_head|tutorial_slides|software_demo|mixed>",
    "title_inferred": "<從影片內容推測的標題>"
  },
  "key_frames": [
    {
      "timestamp": "MM:SS",
      "type": "screenshot",
      "importance": "<high|medium>",
      "description": "<這一幀畫面的具體內容描述>",
      "article_context": "<這張圖在文章中可以用來說明什麼>"
    }
  ],
  "gif_segments": [
    {
      "start_time": "MM:SS",
      "end_time": "MM:SS",
      "description": "<這段動態畫面在展示什麼操作或過程>",
      "article_context": "<這段 GIF 在文章中可以用來說明什麼>"
    }
  ],
  "content_summary": "<100字以內的影片核心內容摘要>",
  "cover_frame": null
}

=== 嚴格規則（違反任何一條將導致任務失敗）===

1. 【絕對禁止純人物畫面 — 零容忍】
   ⚠️ 這是最重要的規則。違反此規則的 key_frame 會被直接刪除。
   嚴禁擷取畫面中「只有講者、觀眾、或舞台」的幀。
   「只有人物」的定義：畫面主體是人（坐著、站著、走動、說話），沒有投影片、圖表、程式碼、UI 等可閱讀的實質資訊。
   即使畫面右下角有講者資訊條（name tag / lower-third），只要畫面主體是人臉/人體，就算「純人物畫面」，禁止擷取。
   ❌ 絕對禁止：講者坐在桌前說話（即使有名牌）、講者站在講台上、攝影機帶到觀眾席、全黑/全白過場畫面。
   ❌ 絕對禁止：講者介紹頁（只有姓名和頭銜、沒有實質內容的畫面）。
   ✅ 正確示範：畫面主體是簡報內容（即使講者在畫面角落 picture-in-picture 也 OK）。
   ✅ 正確示範：投影片佔畫面 70% 以上、講者只在角落小窗。

   整部影片的 key_frames 中，不應該有任何一張是「純人物畫面」。
   如果影片是「講者＋簡報」雙畫面，永遠優先選擇「簡報佔畫面大部分」的時刻。

2. 【只擷取「完成畫面」— 最終狀態，絕對拒絕模糊】
   許多簡報會透過多次點擊逐步展開內容（例如：先顯示標題，再彈出引用、再出現圖表）。
   你「必須只擷取該頁資訊完全展開後的最終狀態」，不要擷取動畫進行中的中間態。
   ❌ 錯誤示範：投影片上的引用框還在滑入、文字還在漸變、圖表正在展開。
   ❌ 錯誤示範：兩頁投影片疊加（過渡動畫中間態）、畫面模糊（運鏡中）、講者遮擋投影片。
   ❌ 絕對拒絕：任何形式的「動態模糊（motion blur）」— 即使部分文字仍可辨識，只要有 blur 痕跡就必須換時間點。
   ✅ 正確示範：所有元素已靜止、文字完整可讀、圖表已完整顯示、畫面銳利無模糊。
   判斷方法：如果同一張投影片在不同時間點「新增了資訊」，請選擇「最完整」的那一幀。
   判斷方法：如果畫面有「任何」區域出現模糊、半透明疊加、或動態殘影，該時間點不可用，必須向前或向後偏移 2-5 秒找完全清晰的幀。

3. 【寧多勿少 — 每張不同的簡報都要抓】
   盡可能抓出「所有」不同的簡報分頁、架構圖切換、或每一次關鍵 UI 操作的最終結果。
   只要畫面上的主要資訊（如投影片標題、程式碼片段、圖表內容）發生了實質性的變化，
   就應該記錄為一個新的 key_frame。

4. 【GIF 嚴格標準】
   gif_segments 只選「動態才有意義」的片段：介面操作示範、狀態切換、程式碼滾動、before/after 比較。
   ❌ 絕對不要做 GIF：純投影片切換、講者手勢、觀眾反應。
   ✅ 適合做 GIF：軟體操作過程、圖表動態展開、程式碼執行結果即時更新。

   【GIF vs 截圖判斷 — 過程重要 vs 結果重要】
   問自己：「讀者需要看到動態過程，還是只需要看到最終結果？」
   ❌ 不適合 GIF（用 key_frame 截取最終畫面即可）：
      - 長時間打字/輸入文字（讀者不需要看人打字，只需要看打完的內容）
      - AI 生成文件/程式碼的滾動過程（最終文件截圖更有資訊量）
      - 頁面緩慢滾動瀏覽（用多張 key_frame 分段截取更清晰）
   ✅ 適合 GIF（動態過程本身就是重點）：
      - 按鈕點擊 → 介面即時反應的互動操作
      - Before/After 狀態切換動畫
      - 圖表/節點動態展開、連線動畫

   【start_time 精確規則 — 這是最常出錯的地方】
   ⚠️ start_time 必須是「動畫內容首個視覺元素出現」的時刻，不是場景切換的時刻。
   常見錯誤：把 start_time 設在投影片過渡動畫（黑屏、漸入、fade）的開始，導致 GIF 前 2-5 秒是黑畫面或講者 talking head。
   ❌ 錯誤：start_time 設在場景切換（黑屏 → 投影片）的黑屏時刻。
   ❌ 錯誤：start_time 設在講者還在說話、投影片尚未出現的時刻。
   ✅ 正確：start_time 設在投影片/圖表的第一個元素已經「可見且清晰」的時刻。
   判斷方法：在 start_time 這一刻截圖，必須看到有意義的視覺內容（文字、圖表、UI），不能是黑屏或講者。

   【end_time 規則】
   ⚠️ end_time 必須設在動畫「完全靜止」之後（所有元素已停止移動），不能在動畫還在進行中就截止。
   寧可多留 1-2 秒，也不要讓動畫截斷。

   【時長硬性限制 — 違反此規則的片段會被自動截斷】
   ❌ 每個 gif_segment 的 (end_time - start_time) 絕對不可超過 12 秒。
   如果動畫本身超過 12 秒，只擷取最精華的 8-12 秒片段，而非試圖涵蓋全部。
   例：一段 30 秒的打字動畫 → 只取中間最密集的 10 秒。
   違反此規則的片段會被腳本自動截斷到 12 秒，導致動畫在未完成時被強制結束。

5. 【去重規則 — key_frames 與 gif_segments 不可重疊】
   同一畫面/時間段只能出現在 key_frames 或 gif_segments 其中之一，禁止兩邊都放。
   - 靜態投影片 → 只放 key_frames
   - 有動態展開/動畫效果 → 只放 gif_segments（不要對同一時間段再加 key_frame）

6. 每個 key_frame 和 gif_segment 都必須有 article_context，說明這個素材在最終文章中的具體用途。
7. 按時間順序排列。
8. 不要輸出任何 JSON 以外的文字。

9. 【封面圖】
   cover_frame 設為 null。封面圖由腳本自動處理（YouTube 影片使用 YouTube 縮圖）。
"""


def is_youtube_url(source: str) -> bool:
    """Check if the source string is a YouTube URL."""
    for pattern in YOUTUBE_URL_PATTERNS:
        if re.match(pattern, source):
            return True
    return False


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract video ID from a YouTube URL."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_youtube_duration(url: str) -> Optional[float]:
    """Get YouTube video duration using yt-dlp."""
    import subprocess
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "duration", url],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.warning("yt-dlp failed to get duration: %s", e)
    return None


def get_video_duration_ffprobe(video_path: str) -> Optional[float]:
    """Get video duration using ffprobe (for local files)."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.warning("ffprobe failed to get duration: %s", e)
    return None


def strip_audio_from_video(video_path: str) -> Optional[str]:
    """Create a copy of the video with audio stripped using ffmpeg.
    
    Returns the path to the stripped video, or None on failure.
    The caller is responsible for cleaning up the temp file.
    """
    import subprocess
    import tempfile
    
    suffix = Path(video_path).suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-an", "-c:v", "copy", tmp_path],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            orig_size = Path(video_path).stat().st_size / (1024 * 1024)
            new_size = Path(tmp_path).stat().st_size / (1024 * 1024)
            logger.info(
                "Audio stripped: %.1f MB -> %.1f MB (saved %.1f MB)",
                orig_size, new_size, orig_size - new_size,
            )
            return tmp_path
        else:
            logger.warning("ffmpeg strip-audio failed: %s", result.stderr[:500])
            Path(tmp_path).unlink(missing_ok=True)
            return None
    except Exception as e:
        logger.warning("ffmpeg strip-audio error: %s", e)
        Path(tmp_path).unlink(missing_ok=True)
        return None


def estimate_tokens(duration_seconds: float) -> int:
    """Estimate token count for default resolution."""
    return int(duration_seconds * TOKENS_PER_SECOND_DEFAULT)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD."""
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_PER_M
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_M
    return round(input_cost + output_cost, 6)


def analyze_video(
    source: str,
    model: str = DEFAULT_MODEL,
    extra_prompt: str = "",
    output_path: Optional[str] = None,
    resolution: str = "LOW",
    keep_file: bool = False,
    strip_audio: bool = False,
) -> Dict[str, Any]:
    """
    Analyze a video using Gemini and return structured JSON.

    Args:
        source: Local file path or YouTube URL
        model: Gemini model to use
        extra_prompt: Additional instructions to append to the prompt
        output_path: Path to write JSON output (optional)
        resolution: Media resolution (LOW or HIGH)
        keep_file: If True, do not delete the uploaded file from Gemini (returns file_name)
        strip_audio: If True, remove audio track before uploading (forces visual-only analysis)

    Returns:
        Dict with analysis results, metadata, and token usage
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _error_result(
            "google-genai SDK not installed. Run: pip install google-genai",
            stage="import",
        )

    # --- Resolve API key ---
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _error_result(
            "GEMINI_API_KEY environment variable not set.",
            stage="auth",
        )

    client = genai.Client(api_key=api_key)

    # --- Build prompt ---
    full_prompt = ANALYSIS_PROMPT
    if extra_prompt:
        full_prompt += f"\n\n額外指示：{extra_prompt}"

    # --- Prepare video input ---
    youtube = is_youtube_url(source)
    file_ref = None
    upload_time = 0
    processing_time = 0
    local_duration = None
    fps = 1.0

    # Track temp files for cleanup
    temp_files_to_clean = []
    original_source = source  # Preserve for YouTube thumbnail extraction

    if youtube:
        logger.info("YouTube URL detected: %s", source)
        local_duration = get_youtube_duration(source)
        if local_duration:
            logger.info("YouTube duration: %.0fs", local_duration)
            if local_duration > 3600:
                fps = 0.5
                logger.info("Duration > 1 hour, setting fps to %.1f", fps)

        if strip_audio:
            # For YouTube + strip_audio: download first, then strip audio and upload
            import subprocess
            import tempfile
            logger.info("Downloading YouTube video for audio stripping...")
            tmp_yt = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            tmp_yt_path = tmp_yt.name
            tmp_yt.close()
            try:
                dl_result = subprocess.run(
                    ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                     "-o", tmp_yt_path, "--force-overwrites", source],
                    capture_output=True, text=True, timeout=300,
                )
                if dl_result.returncode != 0:
                    Path(tmp_yt_path).unlink(missing_ok=True)
                    return _error_result(
                        f"yt-dlp download failed: {dl_result.stderr[:300]}",
                        stage="youtube_download",
                    )
            except Exception as e:
                Path(tmp_yt_path).unlink(missing_ok=True)
                return _error_result(f"yt-dlp download error: {e}", stage="youtube_download")

            temp_files_to_clean.append(tmp_yt_path)
            logger.info("YouTube download complete. Stripping audio...")
            stripped = strip_audio_from_video(tmp_yt_path)
            if stripped:
                temp_files_to_clean.append(stripped)
                source = stripped  # Override source to the stripped file
            else:
                logger.warning("Audio stripping failed, using original with audio")
                source = tmp_yt_path
            youtube = False  # Now treat as local file for upload
        else:
            # Direct YouTube URL pass-through (no strip_audio)
            video_part = types.Part(
                file_data=types.FileData(file_uri=source),
                video_metadata=types.VideoMetadata(fps=fps)
            )
    if not youtube:
        # Local file (or YouTube after download)
        video_path = Path(source).expanduser().resolve()
        if not video_path.exists():
            return _error_result(
                f"Video file not found: {video_path}",
                stage="file_check",
            )
        if not video_path.is_file():
            return _error_result(
                f"Not a file: {video_path}",
                stage="file_check",
            )

        # Strip audio if requested (for local files)
        if strip_audio and source not in [f for f in temp_files_to_clean]:
            logger.info("Stripping audio from local file...")
            stripped = strip_audio_from_video(str(video_path))
            if stripped:
                temp_files_to_clean.append(stripped)
                video_path = Path(stripped)
            else:
                logger.warning("Audio stripping failed, using original with audio")

        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        logger.info("Local file: %s (%.1f MB)", video_path, file_size_mb)

        # Get duration for cost estimation
        if not local_duration:
            local_duration = get_video_duration_ffprobe(str(video_path))
        if local_duration:
            if local_duration > 3600:
                fps = 0.5
                logger.info("Duration > 1 hour, setting fps to %.1f", fps)
            
            est_tokens = estimate_tokens(local_duration)
            est_cost = estimate_cost(est_tokens, 2000)  # ~2K output
            logger.info(
                "Duration: %.0fs | Estimated tokens: %s | Max cost: $%.4f",
                local_duration, f"{est_tokens:,}", est_cost,
            )

        # Upload to File API
        logger.info("Uploading to Gemini File API...")
        t0 = time.time()
        try:
            uploaded_file = client.files.upload(file=str(video_path))
        except Exception as e:
            return _error_result(
                f"File upload failed: {e}",
                stage="upload",
                details={"file_path": str(video_path), "file_size_mb": round(file_size_mb, 1)},
            )
        upload_time = round(time.time() - t0, 1)
        logger.info("Upload complete in %.1fs. File: %s", upload_time, uploaded_file.name)

        # Wait for processing
        logger.info("Waiting for server-side processing...")
        t0 = time.time()
        poll_count = 0
        while uploaded_file.state.name == "PROCESSING":
            poll_count += 1
            if poll_count > 120:  # 10 min timeout
                return _error_result(
                    "File processing timed out after 10 minutes.",
                    stage="processing",
                    details={"file_name": uploaded_file.name},
                )
            time.sleep(5)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            return _error_result(
                f"File processing failed: {getattr(uploaded_file, 'error', 'unknown')}",
                stage="processing",
                details={"file_name": uploaded_file.name},
            )

        processing_time = round(time.time() - t0, 1)
        logger.info("Processing complete in %.1fs. State: %s", processing_time, uploaded_file.state.name)
        file_ref = uploaded_file

        video_part = types.Part(
            file_data=types.FileData(
                file_uri=uploaded_file.uri,
                mime_type=uploaded_file.mime_type,
            ),
            video_metadata=types.VideoMetadata(fps=fps)
        )

    # --- Call Gemini ---
    logger.info("Sending analysis request to %s...", model)
    t0 = time.time()
    # Configure media resolution
    res_level = types.MediaResolution.MEDIA_RESOLUTION_LOW if resolution.upper() == "LOW" else types.MediaResolution.MEDIA_RESOLUTION_HIGH
    config = types.GenerateContentConfig(
        media_resolution=res_level
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=types.Content(
                parts=[video_part, types.Part(text=full_prompt)]
            ),
            config=config,
        )
    except Exception as e:
        err_str = str(e)
        # Provide actionable error messages
        if "quota" in err_str.lower() or "429" in err_str:
            hint = "API quota exceeded. Wait a few minutes or check billing."
        elif "not found" in err_str.lower() or "404" in err_str:
            hint = f"Model '{model}' not found. Try 'gemini-2.5-flash' instead."
        elif "permission" in err_str.lower() or "403" in err_str:
            hint = "API key doesn't have permission for this model/feature."
        elif "too large" in err_str.lower() or "413" in err_str:
            hint = "Video too large for API. Try a shorter clip or lower resolution."
        elif "invalid" in err_str.lower() and "youtube" in err_str.lower():
            hint = "YouTube URL rejected. Video may be private/unlisted or age-restricted."
        else:
            hint = "Check the error details and retry."
        return _error_result(
            f"Gemini API call failed: {e}",
            stage="generate",
            details={"model": model, "hint": hint},
        )
    analysis_time = round(time.time() - t0, 1)
    logger.info("Analysis complete in %.1fs.", analysis_time)

    # --- Extract token usage ---
    usage = getattr(response, "usage_metadata", None)
    token_info = {}
    if usage:
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        total_tokens = getattr(usage, "total_token_count", 0) or (input_tokens + output_tokens)
        cost = estimate_cost(input_tokens, output_tokens)
        token_info = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost,
        }
        logger.info(
            "Tokens — input: %s, output: %s, total: %s | Cost: $%.4f",
            f"{input_tokens:,}", f"{output_tokens:,}", f"{total_tokens:,}", cost,
        )

    # --- Parse JSON response ---
    raw_text = response.text or ""
    # Strip markdown code fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (possibly ```json)
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        # Remove closing fence
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    try:
        analysis = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return _error_result(
            f"Failed to parse Gemini response as JSON: {e}",
            stage="parse",
            details={
                "raw_response_preview": raw_text[:500],
                "parse_error": str(e),
            },
            token_info=token_info,
        )

    # --- Post-process: enforce GIF duration cap (12s) ---
    MAX_GIF_DURATION = 12
    gif_segments = analysis.get("gif_segments", [])
    for seg in gif_segments:
        try:
            s_parts = seg["start_time"].split(":")
            e_parts = seg["end_time"].split(":")
            s_secs = int(s_parts[0]) * 60 + int(s_parts[1])
            e_secs = int(e_parts[0]) * 60 + int(e_parts[1])
            duration = e_secs - s_secs
            if duration > MAX_GIF_DURATION:
                new_end = s_secs + MAX_GIF_DURATION
                seg["end_time"] = f"{new_end // 60:02d}:{new_end % 60:02d}"
                logger.warning(
                    "GIF segment %s→%s was %ds, auto-trimmed to %ds (new end: %s)",
                    seg["start_time"], f"{e_parts[0]}:{e_parts[1]}",
                    duration, MAX_GIF_DURATION, seg["end_time"],
                )
        except (KeyError, ValueError, IndexError):
            pass  # skip malformed segments

    # --- Post-process: cap speaker frames to max 1 ---
    key_frames = analysis.get("key_frames", [])
    speaker_keywords = ["講者", "speaker", "人物", "近景", "自我介紹", "介紹畫面"]
    speaker_frames = [kf for kf in key_frames if any(kw in kf.get("description", "").lower() for kw in speaker_keywords)]
    if len(speaker_frames) > 1:
        # Keep only the first speaker frame, remove the rest
        keep = speaker_frames[0]
        for sf in speaker_frames[1:]:
            key_frames.remove(sf)
            logger.warning("Removed extra speaker frame at %s: %s", sf.get("timestamp"), sf.get("description", "")[:60])
        analysis["key_frames"] = key_frames

    # --- Post-process: cap GIF count to max 5 (keep highest priority) ---
    MAX_GIFS = 5
    gif_segments = analysis.get("gif_segments", [])
    if len(gif_segments) > MAX_GIFS:
        logger.warning("Too many GIFs (%d), trimming to %d", len(gif_segments), MAX_GIFS)
        analysis["gif_segments"] = gif_segments[:MAX_GIFS]

    # --- Post-process: deduplicate key_frames that overlap with gif_segments ---
    gif_segments = analysis.get("gif_segments", [])
    key_frames = analysis.get("key_frames", [])
    gif_ranges = []
    for seg in gif_segments:
        try:
            sp = seg["start_time"].split(":")
            ep = seg["end_time"].split(":")
            gif_ranges.append((int(sp[0]) * 60 + int(sp[1]), int(ep[0]) * 60 + int(ep[1])))
        except (KeyError, ValueError, IndexError):
            pass
    deduped = []
    for kf in key_frames:
        try:
            tp = kf["timestamp"].split(":")
            t_secs = int(tp[0]) * 60 + int(tp[1])
            overlaps = any(gs - 3 <= t_secs <= ge + 3 for gs, ge in gif_ranges)
            if overlaps:
                logger.warning("Removed key_frame at %s (overlaps with GIF range)", kf["timestamp"])
                continue
        except (KeyError, ValueError, IndexError):
            pass
        deduped.append(kf)
    analysis["key_frames"] = deduped

    # --- Build result ---
    result = {
        "success": True,
        "analysis": analysis,
        "metadata": {
            "model": model,
            "source": source,
            "source_type": "youtube" if youtube else "local_file",
            "timing": {
                "upload_seconds": upload_time,
                "processing_seconds": processing_time,
                "analysis_seconds": analysis_time,
                "total_seconds": round(upload_time + processing_time + analysis_time, 1),
            },
            "tokens": token_info,
        },
    }

    if file_ref:
        result["metadata"]["gemini_file_name"] = file_ref.name
        result["metadata"]["gemini_file_uri"] = file_ref.uri

    # Add duration if known
    if local_duration:
        result["metadata"]["video_duration_seconds"] = round(local_duration, 1)

    # Add YouTube thumbnail URL if source is YouTube
    yt_id = extract_youtube_id(original_source)
    if yt_id:
        result["metadata"]["youtube_thumbnail_url"] = f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
        result["metadata"]["youtube_video_id"] = yt_id

    # --- Write output ---
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Output written to: %s", out)

    # --- Cleanup uploaded file (best effort) ---
    if file_ref and not keep_file:
        try:
            client.files.delete(name=file_ref.name)
            logger.info("Cleaned up uploaded file: %s", file_ref.name)
        except Exception as e:
            logger.warning("Could not delete uploaded file: %s", e)
    elif file_ref and keep_file:
        logger.info("File kept in Gemini File API. Name: %s, URI: %s", file_ref.name, file_ref.uri)

    # --- Cleanup temp files ---
    for tmp in temp_files_to_clean:
        try:
            Path(tmp).unlink(missing_ok=True)
            logger.debug("Cleaned up temp file: %s", tmp)
        except Exception:
            pass

    return result


def _error_result(
    message: str,
    stage: str = "unknown",
    details: Optional[Dict] = None,
    token_info: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Build a standardized error result."""
    logger.error("[%s] %s", stage, message)
    result = {
        "success": False,
        "error": {
            "message": message,
            "stage": stage,
        },
    }
    if details:
        result["error"]["details"] = details
    if token_info:
        result["metadata"] = {"tokens": token_info}
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Analyze video using Gemini for key frames and GIF segments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s video.mp4 -o analysis.json
  %(prog)s "https://www.youtube.com/watch?v=XXX" -o analysis.json
  %(prog)s video.mp4 -o analysis.json --extra-prompt "注意 UI 操作畫面"
  %(prog)s video.mp4 -o analysis.json --model gemini-2.5-flash
""",
    )
    parser.add_argument("source", help="Video file path or YouTube URL")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Gemini model (default: {DEFAULT_MODEL})")
    parser.add_argument("--resolution", default="LOW", choices=["LOW", "HIGH"], help="Media resolution for analysis (default: LOW)")
    parser.add_argument("--extra-prompt", default="", help="Additional analysis instructions")
    parser.add_argument("--keep-file", action="store_true", help="Keep the uploaded video file in Gemini for subsequent requests")
    parser.add_argument("--strip-audio", action="store_true", help="Remove audio track before analysis (forces visual-only judgment)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = analyze_video(
        source=args.source,
        model=args.model,
        extra_prompt=args.extra_prompt,
        output_path=args.output,
        resolution=args.resolution,
        keep_file=args.keep_file,
        strip_audio=args.strip_audio,
    )

    # Always print result to stdout
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit with error code if failed
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
