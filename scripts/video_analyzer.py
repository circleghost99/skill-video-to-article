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
你是影片視覺分析專家。請分析這部影片，找出所有值得截圖或製成 GIF 的關鍵畫面。

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
  "content_summary": "<100字以內的影片核心內容摘要>"
}

規則：
1. key_frames 只選「有資訊量」的畫面：UI 介面、架構圖、簡報頁、程式碼、操作結果。純說話的臉不要。
2. gif_segments 只選「動態才有意義」的片段：操作示範、狀態切換、滾動、before/after。靜態的不要做 GIF。
3. 每個 key_frame 和 gif_segment 都必須有 article_context，說明這個素材在文章中的用途。
4. 按時間順序排列。
5. 不要輸出任何 JSON 以外的文字。
"""


def is_youtube_url(source: str) -> bool:
    """Check if the source string is a YouTube URL."""
    for pattern in YOUTUBE_URL_PATTERNS:
        if re.match(pattern, source):
            return True
    return False


def get_video_duration_ffprobe(video_path: str) -> Optional[float]:
    """Get video duration using ffprobe (for local files)."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.warning("ffprobe failed: %s", e)
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
) -> Dict[str, Any]:
    """
    Analyze a video using Gemini and return structured JSON.

    Args:
        source: Local file path or YouTube URL
        model: Gemini model to use
        extra_prompt: Additional instructions to append to the prompt
        output_path: Path to write JSON output (optional)

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

    if youtube:
        logger.info("YouTube URL detected: %s", source)
        video_part = types.Part(
            file_data=types.FileData(file_uri=source)
        )
    else:
        # Local file
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

        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        logger.info("Local file: %s (%.1f MB)", video_path, file_size_mb)

        # Get duration for cost estimation
        local_duration = get_video_duration_ffprobe(str(video_path))
        if local_duration:
            est_tokens = estimate_tokens(local_duration)
            est_cost = estimate_cost(est_tokens, 2000)  # ~2K output
            logger.info(
                "Duration: %.0fs | Estimated tokens: %s | Estimated cost: $%.4f",
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
            )
        )

    # --- Call Gemini ---
    logger.info("Sending analysis request to %s...", model)
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=model,
            contents=types.Content(
                parts=[video_part, types.Part(text=full_prompt)]
            ),
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

    # Add duration if known
    if local_duration:
        result["metadata"]["video_duration_seconds"] = round(local_duration, 1)

    # --- Write output ---
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Output written to: %s", out)

    # --- Cleanup uploaded file (best effort) ---
    if file_ref:
        try:
            client.files.delete(name=file_ref.name)
            logger.info("Cleaned up uploaded file: %s", file_ref.name)
        except Exception as e:
            logger.warning("Could not delete uploaded file: %s", e)

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
    parser.add_argument("--extra-prompt", default="", help="Additional analysis instructions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    result = analyze_video(
        source=args.source,
        model=args.model,
        extra_prompt=args.extra_prompt,
        output_path=args.output,
    )

    # Always print result to stdout
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit with error code if failed
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
