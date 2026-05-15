# CHEONOK Social Signal Scout ALL-IN-ONE SAFE runner
# ASCII only. No Korean text inside this script.
# One command: update scripts -> install deps -> collect -> analyze -> append DB -> open outputs.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_SOCIAL_SIGNAL_ALL_SAFE.ps1 "https://vt.tiktok.com/xxxx/"

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
$ScoutData = Join-Path $Data "social_signal_scout"

$ScriptV02 = Join-Path $Tools "social_signal_scout_v02.py"
$ScriptV03 = Join-Path $Tools "social_signal_scout_v03_analyze.py"
$ScriptV04 = Join-Path $Tools "social_signal_scout_v04_db.py"

$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"

Write-Host "[CHEONOK ALL] START" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null
New-Item -ItemType Directory -Force -Path $ScoutData | Out-Null

Write-Host "[1/7] Update scripts from GitHub" -ForegroundColor Cyan
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v02.py" -OutFile $ScriptV02
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v03_analyze.py" -OutFile $ScriptV03
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v04_db.py" -OutFile $ScriptV04

Write-Host "[2/7] Install/update dependencies" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/7] Collect signal v0.2" -ForegroundColor Cyan
python $ScriptV02 $Url

Write-Host "[4/7] Find latest workdir" -ForegroundColor Cyan
$LatestReport = Get-ChildItem -Path $ScoutData -Filter "report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $LatestReport) {
    Write-Host "[ERROR] report.md not found" -ForegroundColor Red
    exit 1
}

$Workdir = $LatestReport.Directory.FullName
Write-Host "[WORKDIR]" $Workdir -ForegroundColor Green

Write-Host "[5/7] Analyze content v0.3" -ForegroundColor Cyan
python $ScriptV03 $Workdir

Write-Host "[6/7] Append DB v0.4" -ForegroundColor Cyan
python $ScriptV04 $Workdir

Write-Host "[7/7] Open outputs" -ForegroundColor Cyan
$Ideas = Join-Path $Workdir "content_ideas.md"
$IndexMd = Join-Path $ScoutData "social_signal_index.md"
$IndexCsv = Join-Path $ScoutData "social_signal_index.csv"

if (Test-Path $Ideas) {
    notepad $Ideas
}
if (Test-Path $IndexMd) {
    notepad $IndexMd
}

Write-Host "[DONE] content:" $Ideas -ForegroundColor Green
Write-Host "[DONE] index_md:" $IndexMd -ForegroundColor Green
Write-Host "[DONE] index_csv:" $IndexCsv -ForegroundColor Green
