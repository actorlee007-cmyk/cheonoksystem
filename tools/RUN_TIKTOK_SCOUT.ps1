# CHEONOK TikTok Social Signal Scout One-Step Runner
# Safe ASCII version for Windows PowerShell
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_TIKTOK_SCOUT.ps1 "https://vt.tiktok.com/xxxx/"

param(
    [string]$Url = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Url)) {
    $Url = Read-Host "Input TikTok/Shorts/Reels URL"
}

$Base = Join-Path $env:USERPROFILE "Desktop\CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Data = Join-Path $Base "data"
$Script = Join-Path $Tools "social_signal_scout.py"
$RawScriptUrl = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_scout.py"

Write-Host "[CHEONOK] Preparing Social Signal Scout..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null

Write-Host "[1/4] Download scout script" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawScriptUrl -OutFile $Script

Write-Host "[2/4] Install/update yt-dlp" -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install --upgrade yt-dlp

Write-Host "[3/4] Run scout" -ForegroundColor Cyan
python $Script $Url

Write-Host "[4/4] Find latest report.md" -ForegroundColor Cyan
$ScoutData = Join-Path $Data "social_signal_scout"
$Latest = Get-ChildItem -Path $ScoutData -Filter "report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($Latest) {
    Write-Host "[DONE] Report:" $Latest.FullName -ForegroundColor Green
    notepad $Latest.FullName
} else {
    Write-Host "[WARN] report.md not found. Check data folder." -ForegroundColor Yellow
}
