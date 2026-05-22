# CHEONOK FIX ENV AND RUN
# Purpose: fix Windows PowerShell UTF-8 BOM / env read issue, then run YouTube runtime once.

$ErrorActionPreference = 'Stop'

$Root = 'C:\CHEONOK'
$RuntimeDir = Join-Path $Root 'automation\python_youtube_runtime'
$OutputDir = Join-Path $Root '_RUNTIME_OUTPUTS'
$EnvFile = Join-Path $Root '.env'
$RuntimeFile = Join-Path $RuntimeDir 'cheonok_youtube_runtime.py'
$RawRuntimeUrl = 'https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/automation/python_youtube_runtime/cheonok_youtube_runtime.py'

function Write-Step($msg) { Write-Host "[CHEONOK] $msg" -ForegroundColor Cyan }
function Write-Pass($msg) { Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Block($msg) { Write-Host "[BLOCK] $msg" -ForegroundColor Yellow }

New-Item -ItemType Directory -Force -Path $Root, $RuntimeDir, $OutputDir | Out-Null

Write-Step 'Downloading latest Python runtime'
Invoke-WebRequest -Uri $RawRuntimeUrl -OutFile $RuntimeFile -UseBasicParsing

Write-Step 'Reading existing API key safely'
$key = $env:YOUTUBE_API_KEY
if (-not $key -and (Test-Path $EnvFile)) {
  $raw = Get-Content -Raw -Path $EnvFile -Encoding UTF8
  $raw = $raw.TrimStart([char]0xFEFF)
  foreach ($line in ($raw -split "`r?`n")) {
    $clean = $line.Trim().TrimStart([char]0xFEFF)
    if ($clean -match '^YOUTUBE_API_KEY=(.+)$') {
      $key = $Matches[1].Trim()
      break
    }
  }
}

if (-not $key) {
  Write-Host 'Paste restricted/regenerated YouTube API key once.' -ForegroundColor Yellow
  $key = Read-Host 'YOUTUBE_API_KEY'
}

Write-Step 'Writing BOM-free .env'
$envText = "YOUTUBE_API_KEY=$key`nCHEONOK_SITE_URL=https://cheonoksystem.com/cta-5m.html`nCHEONOK_OUTPUT_DIR=$OutputDir`nCHEONOK_MODE=PAPER_ONLY`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($EnvFile, $envText, $utf8NoBom)
$env:YOUTUBE_API_KEY = $key
$env:CHEONOK_SITE_URL = 'https://cheonoksystem.com/cta-5m.html'
$env:CHEONOK_OUTPUT_DIR = $OutputDir
$env:CHEONOK_MODE = 'PAPER_ONLY'
Write-Pass ".env fixed: $EnvFile"

Write-Step 'Running CHEONOK YouTube runtime once'
python $RuntimeFile --root $Root --max-videos 10

Write-Host ''
Write-Pass 'CHEONOK RUNTIME EXECUTION COMPLETE'
Write-Host "REPORTS: $OutputDir"
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
