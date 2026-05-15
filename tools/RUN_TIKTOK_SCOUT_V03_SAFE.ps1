# CHEONOK Social Signal Scout v0.3 SAFE runner
# ASCII only. No Korean text inside this script.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_TIKTOK_SCOUT_V03_SAFE.ps1 "https://vt.tiktok.com/xxxx/"

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
$ScriptV02 = Join-Path $Tools "social_signal_scout_v02.py"
$ScriptV03 = Join-Path $Tools "social_signal_scout_v03_analyze.py"
$RawV02 = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_scout_v02.py"
$RawV03 = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_scout_v03_analyze.py"

Write-Host "[CHEONOK v0.3] START" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null

Write-Host "[1/6] Download scripts" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawV02 -OutFile $ScriptV02
Invoke-WebRequest -Uri $RawV03 -OutFile $ScriptV03

Write-Host "[2/6] Install yt-dlp" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/6] Run scout v0.2" -ForegroundColor Cyan
python $ScriptV02 $Url

Write-Host "[4/6] Find latest workdir" -ForegroundColor Cyan
$ScoutData = Join-Path $Data "social_signal_scout"
$LatestReport = Get-ChildItem -Path $ScoutData -Filter "report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $LatestReport) {
    Write-Host "[ERROR] report.md not found" -ForegroundColor Red
    exit 1
}

$Workdir = $LatestReport.Directory.FullName
Write-Host "[WORKDIR]" $Workdir -ForegroundColor Green

Write-Host "[5/6] Run analyzer v0.3" -ForegroundColor Cyan
python $ScriptV03 $Workdir

Write-Host "[6/6] Open content_ideas.md" -ForegroundColor Cyan
$Ideas = Join-Path $Workdir "content_ideas.md"
if (Test-Path $Ideas) {
    Write-Host "[DONE]" $Ideas -ForegroundColor Green
    notepad $Ideas
} else {
    Write-Host "[WARN] content_ideas.md not found. Opening report.md" -ForegroundColor Yellow
    notepad $LatestReport.FullName
}
