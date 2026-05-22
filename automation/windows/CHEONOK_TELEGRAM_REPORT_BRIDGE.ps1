# CHEONOK TELEGRAM REPORT BRIDGE
# Purpose: send CHEONOK runtime/CEO reports to Telegram with minimum CEO input.
# Safe behavior:
# - Does not store secrets in GitHub.
# - Prompts once for TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, stores locally in C:\CHEONOK\.env.telegram.
# - Sends latest C:\CHEONOK\_RUNTIME_OUTPUTS\*/CEO_REPORT.md.
# - If no report exists, sends a compact fallback status.
# - Installs a Windows scheduled task for recurring delivery.

param(
  [switch]$InstallTask,
  [switch]$Scheduled,
  [int]$IntervalMinutes = 30
)

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = 'C:\CHEONOK'
$OutputDir = Join-Path $Root '_RUNTIME_OUTPUTS'
$LogDir = Join-Path $Root '_REPORT_LOGS'
$EnvTelegram = Join-Path $Root '.env.telegram'
$TaskName = 'CHEONOK_TELEGRAM_REPORT_30M'
$ScriptPath = Join-Path $Root 'CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'

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
      if ($clean -match '^([^#=]+)=(.*)$') {
        $map[$Matches[1].Trim()] = $Matches[2].Trim()
      }
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

function Compact-Message($reportPath) {
  $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  if ($reportPath -and (Test-Path $reportPath.FullName)) {
    $raw = Get-Content -Raw -Path $reportPath.FullName -Encoding UTF8
    $raw = $raw -replace '\r',''
    $lines = $raw -split '\n'
    $important = @()
    foreach ($line in $lines) {
      $t = $line.Trim()
      if ($t -match '^(#|##|TIME_KST|[-*] Runtime|[-*] YouTube API|[-*] Revenue Assets|[-*] Lead|[-*] Payment|[-*] Output|[-*] LIVE_TRADE|[-*] CAPITAL_SCALE|[-*] KIS_ORDER_GATE|[-*] PAPER_ONLY|RUNTIME_STATUS=|YOUTUBE_API_STATUS=|REPORT=|CONTENT_QUEUE=|SEND_READY_POSTS=|BLOCKERS:|FINAL_VETO:)') {
        $important += $t
      }
    }
    if ($important.Count -eq 0) { $important = $lines | Select-Object -First 40 }
    $body = ($important | Select-Object -First 55) -join "`n"
    if ($body.Length -gt 3500) { $body = $body.Substring(0, 3500) + "`n...TRUNCATED" }
    return "[CHEONOK REPORT] $stamp`nPATH: $($reportPath.FullName)`n`n$body"
  }
  return "[CHEONOK REPORT] $stamp`nSTATUS: NO_LOCAL_CEO_REPORT_FOUND`nACTION: Runtime output not found locally. Revenue loop remains focused on cta-5m.html, SEND_READY posts, free diagnosis lead, and 300,000 KRW diagnosis offer.`nFINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE"
}

function Send-Telegram($token, $chatId, $message) {
  $url = "https://api.telegram.org/bot$token/sendMessage"
  $payload = @{
    chat_id = $chatId
    text = $message
    disable_web_page_preview = $true
  }
  try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $payload -TimeoutSec 20
    if ($response.ok -eq $true) { return $true }
    return $false
  } catch {
    Block "Telegram send failed: $($_.Exception.Message)"
    return $false
  }
}

New-Item -ItemType Directory -Force -Path $Root, $OutputDir, $LogDir | Out-Null

$envMap = Read-EnvFile $EnvTelegram
$token = $env:TELEGRAM_BOT_TOKEN
$chatId = $env:TELEGRAM_CHAT_ID
if (-not $token -and $envMap.ContainsKey('TELEGRAM_BOT_TOKEN')) { $token = $envMap['TELEGRAM_BOT_TOKEN'] }
if (-not $chatId -and $envMap.ContainsKey('TELEGRAM_CHAT_ID')) { $chatId = $envMap['TELEGRAM_CHAT_ID'] }

if ((-not $token -or -not $chatId) -and -not $Scheduled) {
  Write-Host ''
  Write-Host 'Telegram report channel needs two one-time values.' -ForegroundColor Yellow
  Write-Host 'Use @BotFather to create a bot token. Send one message to the bot, then use your Telegram user/chat id.' -ForegroundColor Yellow
  if (-not $token) { $token = Read-Host 'TELEGRAM_BOT_TOKEN' }
  if (-not $chatId) { $chatId = Read-Host 'TELEGRAM_CHAT_ID' }
}

if ($token -and $chatId) {
  $envText = "TELEGRAM_BOT_TOKEN=$token`nTELEGRAM_CHAT_ID=$chatId`n"
  Write-NoBom $EnvTelegram $envText
  $latest = Get-LatestReport
  $message = Compact-Message $latest
  $ok = Send-Telegram $token $chatId $message
  $logFile = Join-Path $LogDir ('telegram_report_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
  Write-NoBom $logFile $message
  if ($ok) { Pass "Telegram report sent. Log: $logFile" } else { Block "Telegram report not sent. Log saved: $logFile" }
} else {
  Block 'TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing. Report bridge installed but not connected.'
}

if ($InstallTask -or -not $Scheduled) {
  try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}
  $Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-ExecutionPolicy Bypass -File C:\CHEONOK\CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1 -Scheduled > C:\CHEONOK\_REPORT_LOGS\telegram_task.log 2>&1'
  $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
  $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
  Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
  Pass "Scheduled task installed: $TaskName / every $IntervalMinutes minutes"
}

Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
