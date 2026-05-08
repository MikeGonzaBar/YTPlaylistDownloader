#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv first, then rerun this script." >&2
  exit 1
fi

if ! command -v swift >/dev/null 2>&1; then
  echo "Swift is required for the native macOS frontend. Install Xcode or Command Line Tools first." >&2
  exit 1
fi

cd "$ROOT/macos/PlaylistFolderDownloader"
PFD_BACKEND_ROOT="$ROOT" swift run --scratch-path .swiftpm-cache PlaylistFolderDownloader
