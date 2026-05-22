# CHEONOK TELEGRAM REPORT BRIDGE v3
# Purpose: send executive-grade CHEONOK hourly reports to Telegram with correct Korean UTF-8 encoding.
# Safe behavior:
# - Secrets stay local in C:\CHEONOK\.env.telegram.
# - .env.telegram is the single local source of truth, so stale Windows environment variables do not override it.
# - Sends Telegram payload as UTF-8 JSON, not default Windows form encoding.
# - Schedules at every exact hour.
# - Removes old 30-minute task.

param(
  [switch]$InstallTask,
  [switch]$Scheduled,
  [int]$IntervalMinutes = 60
)

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$Root = 'C:\CHEONOK'
$OutputDir = Join-Path $Root '_RUNTIME_OUTPUTS'
$ReportLogDir = Join-Path $Root '_REPORT_LOGS'
$EnvTelegram = Join-Path $Root '.env.telegram'
$TaskName = 'CHEONOK_TELEGRAM_REPORT_HOURLY'
$OldTaskName = 'CHEONOK_TELEGRAM_REPORT_30M'
$RuntimeTaskName = 'CHEONOK_YOUTUBE_RUNTIME_3H'
$SiteUrl = 'https://cheonoksystem.com/cta-5m.html'

function Step($m) { Write-Host "[CHEONOK] $m" -ForegroundColor Cyan }
function Pass($m) { Write-Host "[PASS] $m" -ForegroundColor Green }
function Block($m) { Write-Host "[BLOCK] $m" -ForegroundColor Yellow }
function Write-NoBom($path, $text) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $text, $utf8NoBom)
}
function Read-EnvFile($path) {
  $map = @{}
  if (Test-Path $path) {
    $raw = Get-Content -Raw -Path $path -Encoding UTF8
    $raw = $raw.TrimStart([char]0xFEFF)
    foreach ($line in ($raw -split "`r?`n")) {
      $clean = $line.Trim().TrimStart([char]0xFEFF)
      if ($clean -match '^([^#=]+)=(.*)$') { $map[$Matches[1].Trim()] = $Matches[2].Trim() }
    }
  }
  return $map
}
function Get-LatestReport() {
  if (-not (Test-Path $OutputDir)) { return $null }
  $reports = Get-ChildItem -Path $OutputDir -Recurse -Filter 'CEO_REPORT.md' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
  if ($reports.Count -eq 0) { return $null }
  return $reports[0]
}
function Get-LatestFile($filter) {
  if (-not (Test-Path $OutputDir)) { return $null }
  $files = Get-ChildItem -Path $OutputDir -Recurse -Filter $filter -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
  if ($files.Count -eq 0) { return $null }
  return $files[0]
}
function Get-TaskState($name) {
  try {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($task) { return $task.State.ToString() }
    return 'NOT_FOUND'
  } catch { return 'UNKNOWN' }
}
function Extract-Line($raw, $pattern, $fallback) {
  foreach ($line in ($raw -split "`r?`n")) {
    $t = $line.Trim()
    if ($t -match $pattern) { return $t }
  }
  return $fallback
}
function Build-ExecutiveMessage($reportPath) {
  $stamp = Get-Date -Format 'yyyy-MM-dd HH:00'
  $posts = Get-LatestFile 'SEND_READY_POSTS.md'
  $queue = Get-LatestFile 'content_queue.csv'
  $json = Get-LatestFile 'youtube_intelligence.json'
  $runtimeTask = Get-TaskState $RuntimeTaskName
  $telegramTask = Get-TaskState $TaskName

  $runtimeStatus = 'UNKNOWN'
  $apiStatus = 'UNKNOWN'
  $assetStatus = 'UNKNOWN'
  $blocker = '없음'
  $outputPath = 'NO_OUTPUT'

  if ($reportPath -and (Test-Path $reportPath.FullName)) {
    $raw = Get-Content -Raw -Path $reportPath.FullName -Encoding UTF8
    $outputPath = $reportPath.DirectoryName
    $runtimeLine = Extract-Line $raw 'Runtime:|RUNTIME_STATUS=' 'Runtime: UNKNOWN'
    $apiLine = Extract-Line $raw 'YouTube API:|YOUTUBE_API_STATUS=' 'YouTube API: UNKNOWN'
    $blockLine = Extract-Line $raw 'API_KEY_SERVICE_BLOCKED|PERMISSION_DENIED|BLOCKED|Block:' 'Block: 없음'
    $runtimeStatus = $runtimeLine -replace '^[-*]\s*',''
    $apiStatus = $apiLine -replace '^[-*]\s*',''
    $blocker = $blockLine -replace '^[-*]\s*',''
  }

  if ($posts -and $queue) { $assetStatus = '생성됨' } else { $assetStatus = '누락 또는 오래됨' }

  $postsPath = if ($posts) { $posts.FullName } else { 'NOT_FOUND' }
  $queuePath = if ($queue) { $queue.FullName } else { 'NOT_FOUND' }
  $jsonPath = if ($json) { $json.FullName } else { 'NOT_FOUND' }

  $msg = @"
[CHEONOK 정시 보고] $stamp KST

1. 결론
- 매출 최우선: 무료진단 1건 → 30만원 실행진단 전환
- 산출물: $assetStatus
- 외부 게시/광고/대량 DM: 승인 전 대기

2. 매출 체인
- CTA: $SiteUrl
- 상품: AI 매출 병목 실행진단 300,000원
- 목표: 리드 20건 / 진단 5건 / 설계 2건 / B2B 1건

3. 런타임
- Runtime: $runtimeStatus
- YouTube API: $apiStatus
- Runtime Task: $runtimeTask
- Telegram Task: $telegramTask

4. 차단/우회
- Blocker: $blocker
- 우회: API 실패 시 오프라인 레퍼런스 기반 SEND_READY 자산 생성 유지

5. 증거
- Output: $outputPath
- Posts: $postsPath
- Queue: $queuePath
- JSON: $jsonPath

6. 다음 정시까지 액션
- SEND_READY 게시문 배포 대기
- 무료진단 신청 1건 확보가 최우선 증거
- 결제 증거 없으면 PASS 금지

7. 승인 필요
- 광고비 집행
- 외부 대량 DM/메일
- 실제 인보이스/청구
- API/Secret/계정 입력
- 실전 주식 주문

Final Veto
LIVE_TRADE=BLOCKED
CAPITAL_SCALE=BLOCKED
KIS_ORDER_GATE=BLOCKED
PAPER_ONLY=TRUE
"@
  if ($msg.Length -gt 3900) { $msg = $msg.Substring(0, 3900) + "`n...TRUNCATED" }
  return $msg
}
function Send-Telegram($token, $chatId, $message) {
  $url = "https://api.telegram.org/bot$token/sendMessage"
  $payload = @{ chat_id = $chatId; text = $message; disable_web_page_preview = $true } | ConvertTo-Json -Depth 5 -Compress
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
  try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $bytes -ContentType 'application/json; charset=utf-8' -TimeoutSec 20
    if ($response.ok -eq $true) { return $true }
    return $false
  } catch {
    Block "Telegram send failed: $($_.Exception.Message)"
    return $false
  }
}
function Get-NextTopOfHour() {
  $now = Get-Date
  $next = $now.AddHours(1)
  return [datetime]::new($next.Year, $next.Month, $next.Day, $next.Hour, 0, 0)
}

New-Item -ItemType Directory -Force -Path $Root, $OutputDir, $ReportLogDir | Out-Null

# .env.telegram is authoritative. Environment variables are fallback only.
$envMap = Read-EnvFile $EnvTelegram
$token = $null
$chatId = $null
if ($envMap.ContainsKey('TELEGRAM_BOT_TOKEN')) { $token = $envMap['TELEGRAM_BOT_TOKEN'] }
if ($envMap.ContainsKey('TELEGRAM_CHAT_ID')) { $chatId = $envMap['TELEGRAM_CHAT_ID'] }
if (-not $token) { $token = $env:TELEGRAM_BOT_TOKEN }
if (-not $chatId) { $chatId = $env:TELEGRAM_CHAT_ID }

if ((-not $token -or -not $chatId) -and -not $Scheduled) {
  Write-Host ''
  Write-Host 'Telegram report channel needs two one-time values.' -ForegroundColor Yellow
  if (-not $token) { $token = Read-Host 'TELEGRAM_BOT_TOKEN' }
  if (-not $chatId) { $chatId = Read-Host 'TELEGRAM_CHAT_ID' }
}

if ($token -and $chatId) {
  Write-NoBom $EnvTelegram "TELEGRAM_BOT_TOKEN=$token`nTELEGRAM_CHAT_ID=$chatId`n"
  $latest = Get-LatestReport
  $message = Build-ExecutiveMessage $latest
  $ok = Send-Telegram $token $chatId $message
  $logFile = Join-Path $ReportLogDir ('telegram_hourly_utf8_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
  Write-NoBom $logFile $message
  if ($ok) { Pass "Telegram executive UTF-8 report sent. Log: $logFile" } else { Block "Telegram report not sent. Log saved: $logFile" }
} else {
  Block 'TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing. Report bridge installed but not connected.'
}

if ($InstallTask -or -not $Scheduled) {
  try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}
  try { Unregister-ScheduledTask -TaskName $OldTaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}
  $Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -File C:\CHEONOK\CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1 -Scheduled > C:\CHEONOK\_REPORT_LOGS\telegram_hourly_task.log 2>&1'
  $Trigger = New-ScheduledTaskTrigger -Once -At (Get-NextTopOfHour) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
  $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
  Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
  Pass "Scheduled task installed: $TaskName / every exact hour"
}

Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
