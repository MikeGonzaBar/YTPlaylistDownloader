param(
  [ValidateSet("Debug", "Release")]
  [string]$Configuration = "Debug",

  [ValidateSet("x64", "x86", "arm64")]
  [string]$Platform = "x64"
)

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ProjectDir "..\..")
$Project = Join-Path $ProjectDir "PlaylistFolderDownloader.csproj"

function Find-Uv {
  if ($env:UV -and (Test-Path $env:UV)) {
    return (Resolve-Path $env:UV).Path
  }

  $command = Get-Command uv -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  $windowsAppsUv = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\uv.exe"
  if (Test-Path $windowsAppsUv) {
    return $windowsAppsUv
  }

  $wingetPackages = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  if (Test-Path $wingetPackages) {
    $uvPackage = Get-ChildItem -Path $wingetPackages -Recurse -Filter uv.exe -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match "astral-sh\.uv" } |
      Select-Object -First 1
    if ($uvPackage) {
      return $uvPackage.FullName
    }
  }

  return $null
}

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
  throw "The .NET SDK is required to run the native Windows frontend."
}

$uvPath = Find-Uv
if ($uvPath) {
  $env:UV = $uvPath
  $env:PATH = "$(Split-Path -Parent $uvPath);$env:PATH"
} else {
  Write-Warning "uv was not found on PATH. The WinUI app can start, but backend load/probe/download calls will fail until uv is available."
}

$env:PFD_BACKEND_ROOT = $RepoRoot
dotnet run --project $Project --configuration $Configuration -p:Platform=$Platform
