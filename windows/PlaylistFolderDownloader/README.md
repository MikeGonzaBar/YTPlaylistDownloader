# Native Windows Frontend

![Playlist Folder Downloader native Windows frontend](../../docs/assets/windows-winui3.png)

This folder is the WinUI 3 / Windows App SDK frontend for Playlist Folder Downloader. It mirrors the native macOS frontend shape:

- load a playlist or single video through the existing Python backend
- auto-probe per-video formats, audio tracks, and subtitles
- edit per-video download options
- apply options to selected rows or all rows
- stream JSON-lines download progress into a queue panel
- cancel running backend work by terminating the Python process tree

The UI uses WinUI controls with Windows 11 Acrylic where supported and falls back to Mica on systems that do not support Acrylic. The app icon is shared with the native macOS frontend.

The backend contract is the same one used by the macOS app:

```powershell
uv run python -m playlist_folder_downloader.cli load <url>
<video-json> | uv run python -m playlist_folder_downloader.cli probe
uv run python -m playlist_folder_downloader.cli download
```

`probe` and `download` receive request JSON on stdin and emit JSON-lines events on stdout. For backward compatibility, the Python CLI still accepts the old positional `probe <video-json>` form, but native frontends should prefer stdin so rich metadata is not exposed through process arguments.

## Requirements

- Windows 10 1809 or later, Windows 11 recommended
- .NET 8 SDK or newer SDK capable of targeting `net8.0-windows`
- Visual Studio 2022 with WinUI / Windows App SDK tooling, or equivalent command-line build tools
- `uv` for dependency installation and as a backend fallback
- the Python backend dependencies installed with `uv sync --extra dev`
- FFmpeg/ffprobe and a JavaScript runtime as described in the root README

At runtime, the app first looks for the repository `.venv\Scripts\python.exe`. If that virtual environment is not available, it falls back to `uv run python`.

## Run

From this folder:

```powershell
.\run.ps1
```

The script sets `PFD_BACKEND_ROOT` to the repository root before launching the WinUI app. You can also run it manually:

```powershell
$env:PFD_BACKEND_ROOT = Resolve-Path ..\..
dotnet run --project .\PlaylistFolderDownloader.csproj --configuration Debug -p:Platform=x64
```

To build without launching:

```powershell
dotnet build .\PlaylistFolderDownloader.csproj -p:Platform=x64
```

## Notes

This is an unpackaged, self-contained Windows App SDK app for local development. If you want Store/MSIX distribution later, add a packaging project or switch the project to packaged deployment.
