# CHEONOK Social Signal Discovery SAFE runner
# ASCII only.
# One command: download discovery script -> update yt-dlp -> find candidates -> analyze top N.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_SOCIAL_DISCOVERY_SAFE.ps1
# powershell -ExecutionPolicy Bypass -File tools\RUN_SOCIAL_DISCOVERY_SAFE.ps1 -Query "Claude Code AI agent startup" -Limit 10 -Analyze 3

param(
    [string]$Query = "",
    [int]$Limit = 5,
    [int]$Analyze = 2
)

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Data = Join-Path $Base "data"
$ScoutData = Join-Path $Data "social_signal_scout"

$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"
$ScriptV02 = Join-Path $Tools "social_signal_scout_v02.py"
$ScriptV03 = Join-Path $Tools "social_signal_scout_v03_analyze.py"
$ScriptV04 = Join-Path $Tools "social_signal_scout_v04_db.py"
$ScriptV05 = Join-Path $Tools "social_signal_discovery_v05.py"

Write-Host "[CHEONOK DISCOVERY] START" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $ScoutData | Out-Null

Write-Host "[1/5] Download latest scripts" -ForegroundColor Cyan
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v02.py" -OutFile $ScriptV02
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v03_analyze.py" -OutFile $ScriptV03
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v04_db.py" -OutFile $ScriptV04
Invoke-WebRequest -Uri "$RawBase/social_signal_discovery_v05.py" -OutFile $ScriptV05

Write-Host "[2/5] Install/update yt-dlp" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/5] Run discovery" -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($Query)) {
    python $ScriptV05 --limit $Limit --analyze $Analyze
} else {
    python $ScriptV05 --query $Query --limit $Limit --analyze $Analyze
}

Write-Host "[4/5] Find latest discovery report" -ForegroundColor Cyan
$DiscoveryDir = Join-Path $ScoutData "discovery"
$Latest = Get-ChildItem -Path $DiscoveryDir -Filter "discovered_candidates.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Write-Host "[5/5] Open report" -ForegroundColor Cyan
if ($Latest) {
    Write-Host "[DONE]" $Latest.FullName -ForegroundColor Green
    notepad $Latest.FullName
} else {
    Write-Host "[WARN] discovered_candidates.md not found" -ForegroundColor Yellow
}
