# CHEONOK INSTALL TELEGRAM REPORT BRIDGE
# Purpose: one-command installer for Telegram report bridge.
# Fixes: local C:\CHEONOK\CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1 missing after GitHub-only patch.

param(
  [int]$IntervalMinutes = 30
)

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = 'C:\CHEONOK'
$LogDir = Join-Path $Root '_REPORT_LOGS'
$BridgePath = Join-Path $Root 'CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'
$BridgeUrl = 'https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/automation/windows/CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'
$TaskName = 'CHEONOK_TELEGRAM_REPORT_30M'

function Step($m) { Write-Host "[CHEONOK] $m" -ForegroundColor Cyan }
function Pass($m) { Write-Host "[PASS] $m" -ForegroundColor Green }
function Block($m) { Write-Host "[BLOCK] $m" -ForegroundColor Yellow }

New-Item -ItemType Directory -Force -Path $Root, $LogDir | Out-Null

Step 'Downloading Telegram report bridge to local runtime folder'
$downloaded = $false
try {
  $cacheBust = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  Invoke-WebRequest -Uri ($BridgeUrl + '?cb=' + $cacheBust) -OutFile $BridgePath -UseBasicParsing -Headers @{ 'Cache-Control'='no-cache' }
  $downloaded = Test-Path $BridgePath
} catch {
  Block "Download failed: $($_.Exception.Message)"
}

if (-not $downloaded) {
  Block 'Telegram bridge could not be downloaded. Local report bridge remains BLOCKED.'
  Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
  exit 1
}

$bridgeText = Get-Content -Raw -Path $BridgePath -Encoding UTF8
if ($bridgeText -notmatch 'CHEONOK TELEGRAM REPORT BRIDGE') {
  Block 'Downloaded bridge failed signature verification.'
  Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
  exit 1
}

Pass "Bridge installed locally: $BridgePath"

Step 'Executing bridge and installing recurring task'
powershell -ExecutionPolicy Bypass -File $BridgePath -InstallTask -IntervalMinutes $IntervalMinutes

Pass 'CHEONOK TELEGRAM REPORT BRIDGE INSTALLER COMPLETE'
Write-Host "RUN_AGAIN: powershell -ExecutionPolicy Bypass -File $BridgePath"
Write-Host "TASK: $TaskName"
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
