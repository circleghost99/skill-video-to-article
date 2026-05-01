#!/bin/bash
# extract_assets.sh — Extract screenshots and GIFs from video based on analysis JSON
#
# Usage:
#   extract_assets.sh <video_path> <analysis_json> [output_dir]
#
# Arguments:
#   video_path     - Path to the source video file
#   analysis_json  - Path to the analysis JSON from video_analyzer.py
#   output_dir     - Output directory (default: ./outputs)
#
# Requires: ffmpeg, jq

set -euo pipefail

# --- Args ---
VIDEO_PATH="${1:-}"
ANALYSIS_JSON="${2:-}"
OUTPUT_DIR="${3:-./outputs}"

if [ -z "$VIDEO_PATH" ] || [ -z "$ANALYSIS_JSON" ]; then
    echo "Usage: extract_assets.sh <video_path> <analysis_json> [output_dir]"
    echo ""
    echo "  video_path     Path to the source video file"
    echo "  analysis_json  Path to analysis JSON from video_analyzer.py"
    echo "  output_dir     Output directory (default: ./outputs)"
    exit 1
fi

# --- Validate inputs ---
if [ ! -f "$VIDEO_PATH" ]; then
    echo "ERROR: Video file not found: $VIDEO_PATH"
    exit 1
fi

if [ ! -f "$ANALYSIS_JSON" ]; then
    echo "ERROR: Analysis JSON not found: $ANALYSIS_JSON"
    exit 1
fi

# Check dependencies
for cmd in ffmpeg jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd is not installed."
        exit 1
    fi
done

# Check that analysis was successful
SUCCESS=$(jq -r '.success' "$ANALYSIS_JSON")
if [ "$SUCCESS" != "true" ]; then
    echo "ERROR: Analysis JSON indicates failure:"
    jq -r '.error.message // "unknown error"' "$ANALYSIS_JSON"
    exit 1
fi

# --- Setup output ---
IMAGES_DIR="$OUTPUT_DIR/images"
mkdir -p "$IMAGES_DIR"

echo "=== Video Asset Extraction ==="
echo "Video:    $VIDEO_PATH"
echo "Analysis: $ANALYSIS_JSON"
echo "Output:   $IMAGES_DIR"
echo ""

# --- Helper: Convert MM:SS to seconds ---
timestamp_to_seconds() {
    local ts="$1"
    local minutes seconds
    minutes=$(echo "$ts" | cut -d: -f1)
    seconds=$(echo "$ts" | cut -d: -f2)
    echo $(( 10#$minutes * 60 + 10#$seconds ))
}

# --- Extract key frames ---
FRAME_COUNT=$(jq -r '.analysis.key_frames | length' "$ANALYSIS_JSON")
echo "--- Key Frames: $FRAME_COUNT ---"

MANIFEST_ENTRIES=()
idx=0

for i in $(seq 0 $(( FRAME_COUNT - 1 ))); do
    ts=$(jq -r ".analysis.key_frames[$i].timestamp" "$ANALYSIS_JSON")
    desc=$(jq -r ".analysis.key_frames[$i].description" "$ANALYSIS_JSON")
    importance=$(jq -r ".analysis.key_frames[$i].importance" "$ANALYSIS_JSON")
    context=$(jq -r ".analysis.key_frames[$i].article_context" "$ANALYSIS_JSON")

    # Convert timestamp for filename (00:03 -> 00m03s)
    ts_safe=$(echo "$ts" | sed 's/:/_/g')
    filename="frame_$(printf '%02d' $((i+1)))_${ts_safe}.jpg"

    echo "  [$((i+1))/$FRAME_COUNT] $ts — $desc"

    # Direct extraction: trust Gemini's timestamp (it already saw the video)
    base_secs=$(timestamp_to_seconds "$ts")
    ffmpeg -ss "$base_secs" -i "$VIDEO_PATH" -vframes 1 -q:v 2 -update 1 \
        "$IMAGES_DIR/$filename" -y -loglevel error 2>/dev/null

    if [ -f "$IMAGES_DIR/$filename" ]; then
        frame_size=$(stat -f%z "$IMAGES_DIR/$filename" 2>/dev/null || stat -c%s "$IMAGES_DIR/$filename" 2>/dev/null || echo "0")
        echo "    → $filename ($(( frame_size / 1024 ))KB)"

        # Build manifest entry
        MANIFEST_ENTRIES+=("$(jq -nc \
            --arg file "$filename" \
            --arg type "screenshot" \
            --arg ts "$ts" \
            --arg desc "$desc" \
            --arg importance "$importance" \
            --arg context "$context" \
            '{file: $file, type: $type, timestamp: $ts, description: $desc, importance: $importance, article_context: $context}')")
    else
        echo "    ⚠️  Failed to extract frame at $ts"
    fi
done

# --- Extract GIF segments ---
GIF_COUNT=$(jq -r '.analysis.gif_segments | length' "$ANALYSIS_JSON")
echo ""
echo "--- GIF Segments: $GIF_COUNT ---"

for i in $(seq 0 $(( GIF_COUNT - 1 ))); do
    [ "$GIF_COUNT" -eq 0 ] && break
    start_ts=$(jq -r ".analysis.gif_segments[$i].start_time" "$ANALYSIS_JSON")
    end_ts=$(jq -r ".analysis.gif_segments[$i].end_time" "$ANALYSIS_JSON")
    desc=$(jq -r ".analysis.gif_segments[$i].description" "$ANALYSIS_JSON")
    context=$(jq -r ".analysis.gif_segments[$i].article_context" "$ANALYSIS_JSON")

    # Calculate duration
    start_secs=$(timestamp_to_seconds "$start_ts")
    end_secs=$(timestamp_to_seconds "$end_ts")
    duration=$(( end_secs - start_secs ))

    if [ "$duration" -le 0 ]; then
        echo "  ⚠️  Skipping invalid GIF segment: $start_ts - $end_ts (duration=$duration)"
        continue
    fi

    # Cap GIF duration at 15 seconds
    if [ "$duration" -gt 15 ]; then
        echo "  ⚠️  GIF segment too long ($duration s), capping at 15s"
        duration=15
    fi

    start_safe=$(echo "$start_ts" | sed 's/:/_/g')
    end_safe=$(echo "$end_ts" | sed 's/:/_/g')
    filename="gif_$(printf '%02d' $((i+1)))_${start_safe}-${end_safe}.gif"

    echo "  [$((i+1))/$GIF_COUNT] $start_ts → $end_ts ($duration s) — $desc"

    # Extract GIF with palette for quality
    ffmpeg -ss "$start_ts" -t "$duration" -i "$VIDEO_PATH" \
        -filter_complex "[0:v] fps=12,scale=720:-1:flags=lanczos,split [a][b];[a] palettegen=max_colors=128 [p];[b][p] paletteuse=dither=bayer" \
        "$IMAGES_DIR/$filename" -y -loglevel warning 2>&1

    if [ $? -eq 0 ] && [ -f "$IMAGES_DIR/$filename" ]; then
        size=$(stat -f%z "$IMAGES_DIR/$filename" 2>/dev/null || stat -c%s "$IMAGES_DIR/$filename" 2>/dev/null || echo "0")
        size_kb=$(( size / 1024 ))
        echo "    → $filename (${size_kb}KB)"

        # Warn if GIF is too large for Discord/web
        if [ "$size_kb" -gt 8192 ]; then
            echo "    ⚠️  GIF is large (${size_kb}KB). Consider shorter clip or lower fps."
        fi

        MANIFEST_ENTRIES+=("$(jq -nc \
            --arg file "$filename" \
            --arg type "gif" \
            --arg start "$start_ts" \
            --arg end "$end_ts" \
            --argjson duration "$duration" \
            --arg desc "$desc" \
            --arg context "$context" \
            '{file: $file, type: $type, start_time: $start, end_time: $end, duration_seconds: $duration, description: $desc, article_context: $context}')")
    else
        echo "    ⚠️  Failed to create GIF for $start_ts → $end_ts"
    fi
done

# --- Write manifest ---
echo ""
echo "--- Writing manifest ---"

# Build manifest JSON
MANIFEST_FILE="$OUTPUT_DIR/manifest.json"
{
    echo "{"
    echo "  \"source_video\": \"$VIDEO_PATH\","
    echo "  \"analysis_json\": \"$ANALYSIS_JSON\","
    echo "  \"generated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","

    # Copy video_info and content_summary from analysis
    echo "  \"video_info\": $(jq -c '.analysis.video_info // {}' "$ANALYSIS_JSON"),"
    echo "  \"content_summary\": $(jq '.analysis.content_summary // ""' "$ANALYSIS_JSON"),"

    # Assets array
    echo "  \"assets\": ["
    for i in "${!MANIFEST_ENTRIES[@]}"; do
        if [ "$i" -lt $(( ${#MANIFEST_ENTRIES[@]} - 1 )) ]; then
            echo "    ${MANIFEST_ENTRIES[$i]},"
        else
            echo "    ${MANIFEST_ENTRIES[$i]}"
        fi
    done
    echo "  ]"
    echo "}"
} | jq '.' > "$MANIFEST_FILE"

TOTAL_ASSETS=${#MANIFEST_ENTRIES[@]}
echo "Manifest: $MANIFEST_FILE ($TOTAL_ASSETS assets)"
echo ""
echo "=== Done ==="
echo "Screenshots: $FRAME_COUNT | GIFs: $GIF_COUNT | Total assets: $TOTAL_ASSETS"
echo "Output dir:  $IMAGES_DIR"
