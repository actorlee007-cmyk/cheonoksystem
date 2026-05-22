# CHEONOK LOCAL BOOTSTRAP
# Purpose: one-command local install/run for CHEONOK YouTube Runtime on Windows.
# This script avoids manual git pull and avoids storing secrets in GitHub.

$ErrorActionPreference = 'Stop'

$Root = 'C:\CHEONOK'
$RuntimeDir = Join-Path $Root 'automation\python_youtube_runtime'
$OutputDir = Join-Path $Root '_RUNTIME_OUTPUTS'
$LogsDir = Join-Path $Root '_RUNTIME_LOGS'
$EnvFile = Join-Path $Root '.env'
$RuntimeFile = Join-Path $RuntimeDir 'cheonok_youtube_runtime.py'
$RawRuntimeUrl = 'https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/automation/python_youtube_runtime/cheonok_youtube_runtime.py'

function Write-Step($msg) { Write-Host "[CHEONOK] $msg" -ForegroundColor Cyan }
function Write-Pass($msg) { Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Block($msg) { Write-Host "[BLOCK] $msg" -ForegroundColor Yellow }

Write-Step 'Creating local folders'
New-Item -ItemType Directory -Force -Path $Root, $RuntimeDir, $OutputDir, $LogsDir | Out-Null

Write-Step 'Checking Python'
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
  Write-Block 'Python is not installed or not in PATH. Install Python 3.11+ once, then re-run this script.'
  exit 2
}
Write-Pass "Python found: $($pythonCmd.Source)"

Write-Step 'Installing Python dependency: requests'
try {
  python -m pip install --upgrade requests | Out-Host
} catch {
  py -m pip install --upgrade requests | Out-Host
}

Write-Step 'Downloading CHEONOK Python runtime from GitHub'
try {
  Invoke-WebRequest -Uri $RawRuntimeUrl -OutFile $RuntimeFile -UseBasicParsing
  Write-Pass "Runtime saved: $RuntimeFile"
} catch {
  Write-Block 'Could not download runtime from GitHub raw URL. Repo may be private or network blocked.'
  Write-Host $_.Exception.Message
  exit 3
}

Write-Step 'Configuring local .env'
$existingKey = $env:YOUTUBE_API_KEY
if (-not $existingKey -and (Test-Path $EnvFile)) {
  $line = Select-String -Path $EnvFile -Pattern '^YOUTUBE_API_KEY=' -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($line) { $existingKey = ($line.Line -replace '^YOUTUBE_API_KEY=', '').Trim() }
}
if (-not $existingKey) {
  Write-Host ''
  Write-Host 'YouTube API key is required once. Paste the restricted/regenerated key below.' -ForegroundColor Yellow
  $existingKey = Read-Host 'YOUTUBE_API_KEY'
}

@"
YOUTUBE_API_KEY=$existingKey
CHEONOK_SITE_URL=https://cheonoksystem.com/cta-5m.html
CHEONOK_OUTPUT_DIR=$OutputDir
CHEONOK_MODE=PAPER_ONLY
"@ | Set-Content -Path $EnvFile -Encoding UTF8
Write-Pass ".env saved: $EnvFile"

$RunBat = Join-Path $Root 'RUN_CHEONOK_YOUTUBE_RUNTIME.bat'
@"
@echo off
cd /d C:\CHEONOK
python automation\python_youtube_runtime\cheonok_youtube_runtime.py --root C:\CHEONOK --max-videos 10
pause
"@ | Set-Content -Path $RunBat -Encoding ASCII

$LoopBat = Join-Path $Root 'START_CHEONOK_YOUTUBE_RUNTIME_LOOP.bat'
@"
@echo off
cd /d C:\CHEONOK
python automation\python_youtube_runtime\cheonok_youtube_runtime.py --root C:\CHEONOK --max-videos 10 --loop-minutes 180
pause
"@ | Set-Content -Path $LoopBat -Encoding ASCII

$TaskPs1 = Join-Path $Root 'INSTALL_CHEONOK_RUNTIME_TASK.ps1'
@"
`$Action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c C:\CHEONOK\RUN_CHEONOK_YOUTUBE_RUNTIME.bat > C:\CHEONOK\_RUNTIME_LOGS\youtube_runtime_task.log 2>&1'
`$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 3) -RepetitionDuration (New-TimeSpan -Days 3650)
`$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'CHEONOK_YOUTUBE_RUNTIME_3H' -Action `$Action -Trigger `$Trigger -Settings `$Settings -Force | Out-Null
Write-Host '[PASS] Windows Scheduled Task installed: CHEONOK_YOUTUBE_RUNTIME_3H'
"@ | Set-Content -Path $TaskPs1 -Encoding UTF8

Write-Step 'Running runtime once now'
try {
  python $RuntimeFile --root $Root --max-videos 10
} catch {
  Write-Block 'Runtime execution failed. See error below.'
  Write-Host $_.Exception.Message
  exit 4
}

Write-Host ''
Write-Pass 'CHEONOK LOCAL RUNTIME INSTALLED AND RAN ONCE'
Write-Host "REPORTS: $OutputDir"
Write-Host "RUN ONCE: $RunBat"
Write-Host "RUN LOOP: $LoopBat"
Write-Host "INSTALL TASK: powershell -ExecutionPolicy Bypass -File $TaskPs1"
Write-Host ''
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
