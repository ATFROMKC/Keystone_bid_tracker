# Creates a clean zip of the Bid Tracker repo for handoff sharing.
# Excludes secrets, venv, caches, build junk, local archives.
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File scripts\make_handoff_zip.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$OutDir = Join-Path $Root "packages"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$ZipPath = Join-Path $OutDir "Keystone_Bid_Tracker_Handoff_$Stamp.zip"

$ExcludeDirNames = @(
    ".git", ".venv", "venv", "__pycache__", ".cursor",
    "_archive", "_local", "build", "dist", "node_modules"
)
$ExcludeFileNames = @(
    "config.json", "msal_token_cache.bin"
)
$ExcludeExtensions = @(".pyc", ".pyo", ".exe", ".zip")

$Temp = Join-Path $env:TEMP "kbt_handoff_stage_$Stamp"
if (Test-Path $Temp) { Remove-Item -Recurse -Force $Temp }
New-Item -ItemType Directory -Force -Path $Temp | Out-Null

function ShouldSkipDir([string]$Name) {
    return $ExcludeDirNames -contains $Name
}

function ShouldSkipFile([System.IO.FileInfo]$File) {
    if ($ExcludeFileNames -contains $File.Name) { return $true }
    if ($ExcludeExtensions -contains $File.Extension.ToLowerInvariant()) { return $true }
    return $false
}

function Copy-Tree([string]$Src, [string]$Dst) {
    New-Item -ItemType Directory -Force -Path $Dst | Out-Null
    Get-ChildItem -LiteralPath $Src -Force | ForEach-Object {
        if ($_.PSIsContainer) {
            if (ShouldSkipDir $_.Name) { return }
            Copy-Tree $_.FullName (Join-Path $Dst $_.Name)
        } else {
            if (ShouldSkipFile $_) { return }
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Dst $_.Name) -Force
        }
    }
}

Write-Host "Staging from $Root ..."
Copy-Tree $Root (Join-Path $Temp "Keystone_Bid_Tracker")

if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $Temp "Keystone_Bid_Tracker") -DestinationPath $ZipPath -CompressionLevel Optimal
Remove-Item -Recurse -Force $Temp

Write-Host "Wrote $ZipPath"
Write-Host "Includes handoff/ docs + source. Excludes config.json, .venv, __pycache__, packages/*.zip, etc."
