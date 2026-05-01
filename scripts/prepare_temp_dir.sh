#!/usr/bin/env bash
# 直接用 bash 執行；開啟 pipefail，避免部分指令失敗被吞掉
set -euo pipefail

PREFIX="${1:-video-to-article}"
BASE_DIR="${TMPDIR:-/tmp}/openclaw-video-to-article"
mkdir -p "$BASE_DIR"
RUN_ID="${PREFIX}-$(date +%Y%m%d-%H%M%S)-$$"
RUN_DIR="$BASE_DIR/$RUN_ID"
mkdir -p "$RUN_DIR" "$RUN_DIR/frames" "$RUN_DIR/final"
printf '%s\n' "$RUN_DIR"
