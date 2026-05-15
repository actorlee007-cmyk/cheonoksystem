# CHEONOK TikTok Social Signal Scout - SAFE runner
# ASCII only. No Korean text inside this script.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_TIKTOK_SCOUT_SAFE.ps1 "https://vt.tiktok.com/xxxx/"

param(
    [string]$Url = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Url)) {
    $Url = Read-Host "Input URL"
}

$Base = Join-Path $env:USERPROFILE "Desktop\CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Data = Join-Path $Base "data"
$Script = Join-Path $Tools "social_signal_scout.py"
$RawScriptUrl = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_scout.py"

Write-Host "[CHEONOK] START" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null

Write-Host "[1/4] Download python scout" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawScriptUrl -OutFile $Script

Write-Host "[2/4] Install yt-dlp" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/4] Run scout" -ForegroundColor Cyan
python $Script $Url

Write-Host "[4/4] Open latest report" -ForegroundColor Cyan
$ScoutData = Join-Path $Data "social_signal_scout"
$Latest = Get-ChildItem -Path $ScoutData -Filter "report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($Latest) {
    Write-Host "[DONE]" $Latest.FullName -ForegroundColor Green
    notepad $Latest.FullName
} else {
    Write-Host "[WARN] report not found" -ForegroundColor Yellow
}
