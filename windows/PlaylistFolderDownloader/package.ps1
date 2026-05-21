param(
  [ValidateSet("Release", "Debug")]
  [string]$Configuration = "Release",

  [ValidateSet("x64", "x86", "arm64")]
  [string]$Platform = "x64"
)

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ProjectDir "..\..")
$Project = Join-Path $ProjectDir "PlaylistFolderDownloader.csproj"
$Runtime = "win-$Platform"

dotnet build $Project --configuration $Configuration -p:Platform=$Platform -r $Runtime --self-contained true

$BuildOutput = Join-Path $ProjectDir "bin\$Platform\$Configuration\net8.0-windows10.0.19041.0\$Runtime"
$DistRoot = Join-Path $RepoRoot "dist"
$PortableDir = Join-Path $DistRoot "PlaylistFolderDownloader-WinUI3-$Runtime"
$ZipPath = "$PortableDir.zip"

if (Test-Path $PortableDir) {
  $ResolvedPortableDir = (Resolve-Path $PortableDir).Path
  if (-not $ResolvedPortableDir.StartsWith($RepoRoot.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove outside workspace: $ResolvedPortableDir"
  }
  Remove-Item -LiteralPath $ResolvedPortableDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $PortableDir | Out-Null
Get-ChildItem -LiteralPath $BuildOutput -Force |
  Where-Object { $_.Name -ne "publish" } |
  ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $PortableDir -Recurse -Force
  }

if (Test-Path $ZipPath) {
  Remove-Item -LiteralPath $ZipPath -Force
}

Compress-Archive -Path (Join-Path $PortableDir "*") -DestinationPath $ZipPath

Write-Host "Portable app: $PortableDir"
Write-Host "Zip archive:  $ZipPath"
