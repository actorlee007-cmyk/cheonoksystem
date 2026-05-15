# CHEONOK Social Signal Scout v0.2 SAFE runner
# ASCII only. No Korean text inside this script.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_TIKTOK_SCOUT_V02_SAFE.ps1 "https://vt.tiktok.com/xxxx/"

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
$Script = Join-Path $Tools "social_signal_scout_v02.py"
$RawScriptUrl = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_scout_v02.py"

Write-Host "[CHEONOK v0.2] START" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null

Write-Host "[1/5] Download python scout v0.2" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawScriptUrl -OutFile $Script

Write-Host "[2/5] Install yt-dlp" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/5] Run scout v0.2" -ForegroundColor Cyan
python $Script $Url

Write-Host "[4/5] Find latest report" -ForegroundColor Cyan
$ScoutData = Join-Path $Data "social_signal_scout"
$Latest = Get-ChildItem -Path $ScoutData -Filter "report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Write-Host "[5/5] Open report" -ForegroundColor Cyan
if ($Latest) {
    Write-Host "[DONE]" $Latest.FullName -ForegroundColor Green
    notepad $Latest.FullName
} else {
    Write-Host "[WARN] report not found" -ForegroundColor Yellow
}
