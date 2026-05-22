# CHEONOK FORCE RUNTIME REPAIR
# One-command repair for Windows local runtime.
# - Removes old scheduled task that may keep running stale code
# - Downloads latest v2 runtime with cache-bust
# - Verifies runtime contains API-block fallback logic
# - Runs once
# - If YouTube API is blocked, still creates revenue assets
# - Reinstalls 3-hour scheduled task using this repair script

param(
  [switch]$Scheduled
)

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = 'C:\CHEONOK'
$RuntimeDir = Join-Path $Root 'automation\python_youtube_runtime'
$OutputDir = Join-Path $Root '_RUNTIME_OUTPUTS'
$LogsDir = Join-Path $Root '_RUNTIME_LOGS'
$EnvFile = Join-Path $Root '.env'
$RuntimeFile = Join-Path $RuntimeDir 'cheonok_youtube_runtime.py'
$RepairFile = Join-Path $Root 'CHEONOK_FORCE_RUNTIME_REPAIR.ps1'
$TaskName = 'CHEONOK_YOUTUBE_RUNTIME_3H'
$RawRuntimeUrlBase = 'https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/automation/python_youtube_runtime/cheonok_youtube_runtime.py'

function Step($m) { Write-Host "[CHEONOK] $m" -ForegroundColor Cyan }
function Pass($m) { Write-Host "[PASS] $m" -ForegroundColor Green }
function Block($m) { Write-Host "[BLOCK] $m" -ForegroundColor Yellow }

function Write-NoBom($path, $text) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $text, $utf8NoBom)
}

function Get-EnvKey() {
  $key = $env:YOUTUBE_API_KEY
  if (-not $key -and (Test-Path $EnvFile)) {
    $raw = Get-Content -Raw -Path $EnvFile -Encoding UTF8
    $raw = $raw.TrimStart([char]0xFEFF)
    foreach ($line in ($raw -split "`r?`n")) {
      $clean = $line.Trim().TrimStart([char]0xFEFF)
      if ($clean -match '^YOUTUBE_API_KEY=(.+)$') { return $Matches[1].Trim() }
    }
  }
  return $key
}

function Create-FallbackOutputs($reason) {
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $dir = Join-Path $OutputDir $stamp
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $site = 'https://cheonoksystem.com/cta-5m.html'

  $posts = @"
# SEND READY POSTS

## Threads/X

조회수는 있는데 문의가 없다면 콘텐츠 문제가 아닐 수 있습니다.

대부분은 '다음 행동'이 안 보이는 구조 문제입니다.
첫 문장, 신뢰, 상품, 결제 버튼 중 하나가 끊기면 사람은 보고도 지나갑니다.

링크 하나 보내면 막힌 지점 1개를 무료로 봅니다.
$site

---

## Naver Blog/Cafe

제목: 홈페이지는 있는데 문의가 없는 이유

홈페이지가 있어도 문의가 없다면 디자인보다 흐름을 봐야 합니다.
방문자는 예쁜 페이지를 결제하지 않습니다.
자기 문제가 이해받고, 결과물이 선명하고, 위험이 낮고, 다음 행동이 쉬울 때 움직입니다.

링크 하나만 보내주시면 막힌 지점 1개를 무료로 진단합니다.
$site

---

## B2B DM Draft

안녕하세요. 천옥시스템입니다.

홈페이지/채널/상품 페이지를 운영 중인데 문의나 결제로 이어지지 않는 경우, 대부분은 디자인보다 고객의 다음 행동이 끊긴 구조에서 문제가 생깁니다.

링크 하나만 주시면 매출 병목 1개와 바로 고칠 행동 1개를 무료로 정리해드리겠습니다.
"@
  Write-NoBom (Join-Path $dir 'SEND_READY_POSTS.md') $posts

  $csv = @"
Status,Asset Type,Title,Hook,Body,CTA,Cash Chain,Risk Veto,Source,Revenue Link
SEND_READY,SHORTS_SCRIPT,AI를 써도 매출이 안 나는 진짜 이유,""열심히 만들었는데 문의가 없다면 고객이 다음 행동을 못 찾는 겁니다."",""AI는 더 많이 만드는 도구가 아니라 끊긴 매출 루프를 이어주는 운영자입니다."",""링크 하나 보내면 무료로 봅니다. $site"",Exposure -> Lead,""수익 보장/허위 인증 금지"",CHEONOK Fallback,$site
SEND_READY,Threads/X revenue post,""조회수는 있는데 문의가 없는 이유"",""조회수는 있는데 문의가 없다면 콘텐츠 문제가 아닐 수 있습니다."",""다음 행동이 안 보이는 구조 문제입니다."",$site,Exposure -> Lead,""외부 대량 발송은 대표 승인 필요"",5M Revenue Sprint,$site
"@
  Write-NoBom (Join-Path $dir 'content_queue.csv') $csv

  $json = @{
    generated_at_kst = (Get-Date).ToString('s')
    runtime_status = 'FALLBACK_REVENUE_ASSETS_GENERATED'
    api_status = $reason
    mode = 'PAPER_ONLY'
    site_url = $site
    final_veto = @{ LIVE_TRADE='BLOCKED'; CAPITAL_SCALE='BLOCKED'; KIS_ORDER_GATE='BLOCKED'; PAPER_ONLY=$true }
  } | ConvertTo-Json -Depth 5
  Write-NoBom (Join-Path $dir 'youtube_intelligence.json') $json

  $report = @"
# CHEONOK Runtime CEO Report

TIME_KST: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## VERDICT
- Runtime: FALLBACK_REVENUE_ASSETS_GENERATED
- Block: $reason
- Revenue Assets: GENERATED
- YouTube API 실패는 매출 실행을 멈추지 않음.

## CASH CHAIN
- Exposure: 쇼츠/게시문 생성
- Lead: $site
- Payment: 300,000 KRW AI 매출 병목 실행진단
- Delivery: 진단 리포트 납품
- Exit Ledger: JSON/CSV/Markdown 기록

## FINAL VETO
- LIVE_TRADE: BLOCKED
- CAPITAL_SCALE: BLOCKED
- KIS_ORDER_GATE: BLOCKED
- PAPER_ONLY: TRUE
"@
  Write-NoBom (Join-Path $dir 'CEO_REPORT.md') $report
  Pass "Fallback revenue assets created: $dir"
  return $dir
}

Step 'Creating folders'
New-Item -ItemType Directory -Force -Path $Root, $RuntimeDir, $OutputDir, $LogsDir | Out-Null

Step 'Removing stale scheduled task if present'
try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}

Step 'Downloading latest runtime with cache-bust'
$runtimeUrl = $RawRuntimeUrlBase + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
try {
  Invoke-WebRequest -Uri $runtimeUrl -OutFile $RuntimeFile -UseBasicParsing -Headers @{ 'Cache-Control'='no-cache' }
} catch {
  Block "Download failed: $($_.Exception.Message)"
  Create-FallbackOutputs 'RUNTIME_DOWNLOAD_FAILED' | Out-Null
}

$validRuntime = $false
if (Test-Path $RuntimeFile) {
  $runtimeText = Get-Content -Raw -Path $RuntimeFile -Encoding UTF8
  if ($runtimeText -match 'CHEONOK YouTube Runtime Engine v2' -and $runtimeText -match 'API_BLOCKED_OFFLINE_REVENUE_ASSETS_GENERATED') {
    $validRuntime = $true
    Pass "Runtime v2 verified: $RuntimeFile"
  }
}

if (-not $validRuntime) {
  Block 'Runtime file is stale or invalid. Generating fallback revenue assets now.'
  Create-FallbackOutputs 'STALE_RUNTIME_FILE' | Out-Null
} else {
  $key = Get-EnvKey
  if (-not $key -and -not $Scheduled) {
    Write-Host 'Paste restricted/regenerated YouTube API key once.' -ForegroundColor Yellow
    $key = Read-Host 'YOUTUBE_API_KEY'
  }
  if ($key) {
    $envText = "YOUTUBE_API_KEY=$key`nCHEONOK_SITE_URL=https://cheonoksystem.com/cta-5m.html`nCHEONOK_OUTPUT_DIR=$OutputDir`nCHEONOK_MODE=PAPER_ONLY`n"
    Write-NoBom $EnvFile $envText
    $env:YOUTUBE_API_KEY = $key
  }
  $env:CHEONOK_SITE_URL = 'https://cheonoksystem.com/cta-5m.html'
  $env:CHEONOK_OUTPUT_DIR = $OutputDir
  $env:CHEONOK_MODE = 'PAPER_ONLY'

  Step 'Running runtime once'
  $logFile = Join-Path $LogsDir ('force_runtime_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
  try {
    $out = & python $RuntimeFile --root $Root --max-videos 10 2>&1
    $out | Tee-Object -FilePath $logFile
    $outText = ($out | Out-String)
    if ($outText -match 'V3Data.*blocked|API_KEY_SERVICE|PERMISSION_DENIED') {
      Block 'Raw YouTube API block text detected. Creating clean fallback outputs too.'
      Create-FallbackOutputs 'YOUTUBE_API_PERMISSION_DENIED' | Out-Null
    }
  } catch {
    Block "Python runtime failed: $($_.Exception.Message)"
    Create-FallbackOutputs 'PYTHON_RUNTIME_FAILED' | Out-Null
  }
}

Step 'Writing local run files'
$RunBat = Join-Path $Root 'RUN_CHEONOK_YOUTUBE_RUNTIME.bat'
@"
@echo off
cd /d C:\CHEONOK
powershell -ExecutionPolicy Bypass -File C:\CHEONOK\CHEONOK_FORCE_RUNTIME_REPAIR.ps1
pause
"@ | Set-Content -Path $RunBat -Encoding ASCII

$LoopBat = Join-Path $Root 'START_CHEONOK_YOUTUBE_RUNTIME_LOOP.bat'
@"
@echo off
cd /d C:\CHEONOK
:loop
powershell -ExecutionPolicy Bypass -File C:\CHEONOK\CHEONOK_FORCE_RUNTIME_REPAIR.ps1 -Scheduled
 timeout /t 10800 /nobreak
 goto loop
"@ | Set-Content -Path $LoopBat -Encoding ASCII

Step 'Installing clean 3-hour scheduled task'
$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-ExecutionPolicy Bypass -File C:\CHEONOK\CHEONOK_FORCE_RUNTIME_REPAIR.ps1 -Scheduled > C:\CHEONOK\_RUNTIME_LOGS\youtube_runtime_task.log 2>&1'
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 3) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null

Pass 'CHEONOK FORCE RUNTIME REPAIR COMPLETE'
Write-Host "REPORTS: $OutputDir"
Write-Host "RUN: $RunBat"
Write-Host "TASK: $TaskName"
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
