#!/usr/bin/env bash
# zsh 沒有 pipefail，OpenClaw exec 預設 zsh，用 set -euo 即可
set -euo

BASE_DIR="${1:-${TMPDIR:-/tmp}/openclaw-video-to-article}"
TTL_HOURS="${2:-24}"

if [[ ! -d "$BASE_DIR" ]]; then
  echo "[cleanup] no temp dir: $BASE_DIR"
  exit 0
fi

find "$BASE_DIR" -mindepth 1 -maxdepth 1 -type d -mtime "+$(( TTL_HOURS / 24 ))" -print -exec rm -rf {} +
