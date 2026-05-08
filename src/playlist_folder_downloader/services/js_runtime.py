"""JavaScript runtime detection for yt-dlp's YouTube extractor."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


def find_js_runtime() -> tuple[str | None, str | None]:
    """Find a JavaScript runtime supported by yt-dlp.

    yt-dlp enables Deno by default, but Node is commonly available on developer
    Macs via nvm/homebrew. Prefer Deno when present because yt-dlp gives it the
    highest priority, then fall back to Node.
    """

    for runtime in ("deno", "node"):
        path = shutil.which(runtime)
        if path:
            return runtime, path

    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.exists():
        candidates = sorted(nvm_root.glob("v*/bin/node"), reverse=True)
        for candidate in candidates:
            if candidate.exists():
                return "node", str(candidate)

    return None, None


def build_js_runtime_options() -> dict[str, Any]:
    """Return yt-dlp options enabling a detected JS runtime."""

    runtime, path = find_js_runtime()
    if not runtime:
        return {}
    return {"js_runtimes": {runtime: {"path": path}}}
