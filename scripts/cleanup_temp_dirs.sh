#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${1:-${TMPDIR:-/tmp}/openclaw-video-to-article}"
TTL_HOURS="${2:-24}"

if [[ ! -d "$BASE_DIR" ]]; then
  echo "[cleanup] no temp dir: $BASE_DIR"
  exit 0
fi

find "$BASE_DIR" -mindepth 1 -maxdepth 1 -type d -mtime "+$(( TTL_HOURS / 24 ))" -print -exec rm -rf {} +
