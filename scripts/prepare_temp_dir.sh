#!/usr/bin/env bash
set -euo pipefail

PREFIX="${1:-video-to-article}"
BASE_DIR="${TMPDIR:-/tmp}/openclaw-video-to-article"
mkdir -p "$BASE_DIR"
RUN_ID="${PREFIX}-$(date +%Y%m%d-%H%M%S)-$$"
RUN_DIR="$BASE_DIR/$RUN_ID"
mkdir -p "$RUN_DIR" "$RUN_DIR/frames" "$RUN_DIR/final"
printf '%s\n' "$RUN_DIR"
