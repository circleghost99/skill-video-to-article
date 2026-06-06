#!/usr/bin/env python3
"""
frame_aligner.py — Micro-alignment of Video Key Frames using Laplacian Variance and Frame Difference.

This script takes a target video, a rough timestamp, and extracts the most optimal
(clearest, most stable/static) frame within a small search window (e.g., ±2 seconds).
This resolves issues where Gemini returns a timestamp that falls on a transition or motion blur.

Usage:
    python3 frame_aligner.py <video_path> <timestamp_mm_ss> <output_path> [options]

Requirements:
    pip install opencv-python Pillow
"""

import argparse
import sys
import os
import re
from pathlib import Path
import numpy as np

# Try to import cv2
try:
    import cv2
except ImportError:
    print("ERROR: opencv-python is not installed. Run: pip install opencv-python", file=sys.stderr)
    sys.exit(1)


def parse_timestamp(ts_str: str) -> float:
    """Convert MM:SS or float string to seconds."""
    if ":" in ts_str:
        parts = ts_str.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return float(ts_str)


def format_seconds(seconds: float) -> str:
    """Format seconds back to MM:SS."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"


def get_optimal_frame(
    video_path: str,
    target_time: float,
    window_sec: float = 2.0,
    step_sec: float = 0.2,
) -> tuple[np.ndarray, float, dict]:
    """
    Scans the window around target_time and finds the clearest (highest Laplacian var)
    and most stable (lowest local difference) frame.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    start_time = max(0.0, target_time - window_sec)
    end_time = min(duration, target_time + window_sec) if duration > 0 else target_time + window_sec

    # Collect frames and their stats
    candidates = []
    current_time = start_time
    
    prev_gray = None

    while current_time <= end_time:
        frame_idx = int(current_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            current_time += step_sec
            continue

        # Calculate sharpness (Laplacian variance)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Calculate frame difference to check for stability
        diff_val = 0.0
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            diff_val = diff.mean()

        candidates.append({
            "time": current_time,
            "frame": frame,
            "gray": gray,
            "sharpness": lap_var,
            "difference_with_prev": diff_val
        })

        prev_gray = gray
        current_time += step_sec

    cap.release()

    if not candidates:
        raise ValueError(f"No frames could be extracted around {target_time}s")

    # Algorithm to select the best frame:
    # 1. Identify "stable" frames where the difference with the previous frame is low.
    #    This filters out transition/motion blur frames.
    # 2. Within those stable zones, select the frame with the highest sharpness (Laplacian variance).
    # 3. If everything is changing (e.g. video/animation), fallback to the absolute sharpest frame.
    
    # Calculate a threshold for "stable" frame difference
    # Frame difference is only valid from the 2nd candidate onwards
    diffs = [c["difference_with_prev"] for c in candidates[1:]] if len(candidates) > 1 else []
    
    stable_candidates = []
    if diffs:
        # We define a transition threshold as 1.5 times the median difference or a flat minimum
        median_diff = np.median(diffs)
        # Frames with a difference lower than this threshold are considered static
        threshold = max(2.0, median_diff * 1.2)
        
        # The first frame has no difference_with_prev. We assign it the second frame's value
        # or median to avoid penalizing it.
        candidates[0]["difference_with_prev"] = candidates[1]["difference_with_prev"] if len(candidates) > 1 else 0.0
        
        stable_candidates = [c for c in candidates if c["difference_with_prev"] <= threshold]

    # Fallback to all candidates if no stable zones found (highly dynamic scene)
    pool = stable_candidates if stable_candidates else candidates

    # Find the one with maximum sharpness
    best_candidate = max(pool, key=lambda x: x["sharpness"])
    
    metadata = {
        "original_timestamp": format_seconds(target_time),
        "selected_timestamp": format_seconds(best_candidate["time"]),
        "offset_seconds": round(best_candidate["time"] - target_time, 2),
        "sharpness": round(best_candidate["sharpness"], 2),
        "total_scanned_frames": len(candidates),
        "stable_frames_count": len(stable_candidates),
    }

    return best_candidate["frame"], best_candidate["time"], metadata


def main():
    parser = argparse.ArgumentParser(description="Extract the optimal/clearest video frame around a timestamp.")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("timestamp", help="Rough timestamp in MM:SS or seconds")
    parser.add_argument("output", help="Path to save the output image (.jpg)")
    parser.add_argument("--window", type=float, default=2.0, help="Search window in seconds around timestamp (default: 2.0)")
    parser.add_argument("--step", type=float, default=0.2, help="Scan step in seconds (default: 0.2)")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"ERROR: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    try:
        target_sec = parse_timestamp(args.timestamp)
    except ValueError:
        print(f"ERROR: Invalid timestamp format: {args.timestamp}", file=sys.stderr)
        sys.exit(1)

    print(f"Aligning frame for {args.timestamp} (parsed: {target_sec}s)...")
    
    try:
        best_frame, best_time, meta = get_optimal_frame(
            video_path=args.video,
            target_time=target_sec,
            window_sec=args.window,
            step_sec=args.step
        )
        
        # Create output parent dirs
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save frame
        cv2.imwrite(str(out_path), best_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        
        print("Success!")
        print(f"  Original: {meta['original_timestamp']}s")
        print(f"  Selected: {meta['selected_timestamp']}s (Offset: {meta['offset_seconds']}s)")
        print(f"  Sharpness (Laplacian var): {meta['sharpness']}")
        print(f"  Scanned:  {meta['total_scanned_frames']} frames")
        
    except Exception as e:
        print(f"ERROR: Frame extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
