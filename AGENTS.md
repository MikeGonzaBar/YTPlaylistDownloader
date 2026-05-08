# Playlist Folder Downloader Coding Rules

- Keep the app cross-platform and use standard Python or Qt APIs unless a packaging script is intentionally platform-specific.
- Do not implement DRM bypasses, signature-bypass hacks, account-cookie stealing, private-video scraping, CAPTCHA bypass, credential collection, or other access-control bypasses.
- Keep network-dependent and yt-dlp functionality behind service classes.
- Tests must not hit YouTube or download real media.
- Use mocks and fixtures for yt-dlp metadata tests.
- Keep the GUI responsive; no blocking network or download work may run on the main Qt thread.
- Prefer small, typed, testable functions.
- Do not store cookies, user credentials, signed media URLs, or telemetry.
- Run `python scripts/check_env.py`, `python -m pytest -q`, and `python -m ruff check .` before the final response.
