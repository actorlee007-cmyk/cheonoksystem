# CHEONOK TELEGRAM CONNECT WIZARD
# Purpose: fix Telegram 401 Unauthorized by validating bot token, discovering chat_id, saving local config, sending test report, and installing recurring report task.
# Secrets stay local in C:\CHEONOK\.env.telegram only.

param(
  [int]$IntervalMinutes = 30
)

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = 'C:\CHEONOK'
$LogDir = Join-Path $Root '_REPORT_LOGS'
$EnvTelegram = Join-Path $Root '.env.telegram'
$BridgePath = Join-Path $Root 'CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'
$BridgeUrl = 'https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/automation/windows/CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'

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
function Validate-Token($token) {
  try {
    $r = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getMe" -Method Get -TimeoutSec 20
    if ($r.ok -eq $true) { return $r.result }
    return $null
  } catch {
    return $null
  }
}
function Get-ChatId($token) {
  try {
    $r = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getUpdates" -Method Get -TimeoutSec 20
    if ($r.ok -ne $true) { return $null }
    $items = @($r.result)
    if ($items.Count -eq 0) { return $null }
    $latest = $items | Sort-Object update_id -Descending | Select-Object -First 1
    if ($latest.message.chat.id) { return [string]$latest.message.chat.id }
    if ($latest.my_chat_member.chat.id) { return [string]$latest.my_chat_member.chat.id }
    if ($latest.channel_post.chat.id) { return [string]$latest.channel_post.chat.id }
    return $null
  } catch {
    return $null
  }
}
function Send-Test($token, $chatId) {
  $msg = "[CHEONOK TELEGRAM CONNECTED]`nREPORT_BRIDGE=ACTIVE`nINTERVAL_MINUTES=$IntervalMinutes`nFINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE"
  try {
    $r = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/sendMessage" -Method Post -Body @{ chat_id=$chatId; text=$msg; disable_web_page_preview=$true } -TimeoutSec 20
    return ($r.ok -eq $true)
  } catch {
    Block "Test send failed: $($_.Exception.Message)"
    return $false
  }
}

New-Item -ItemType Directory -Force -Path $Root, $LogDir | Out-Null

Step 'Downloading latest Telegram report bridge'
try {
  $cb = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  Invoke-WebRequest -Uri ($BridgeUrl + '?cb=' + $cb) -OutFile $BridgePath -UseBasicParsing -Headers @{ 'Cache-Control'='no-cache' }
  Pass "Bridge ready: $BridgePath"
} catch {
  Block "Bridge download failed: $($_.Exception.Message)"
}

$envMap = Read-EnvFile $EnvTelegram
$oldToken = $envMap['TELEGRAM_BOT_TOKEN']
$oldChatId = $envMap['TELEGRAM_CHAT_ID']

$token = $oldToken
$bot = $null
if ($token) { $bot = Validate-Token $token }

if (-not $bot) {
  Write-Host ''
  Block 'Existing Telegram token is missing or invalid. 401 Unauthorized means the BOT TOKEN is wrong, not the chat id.'
  Write-Host 'Paste the full token from @BotFather. It must look like 1234567890:ABCDEF... including the colon.' -ForegroundColor Yellow
  $token = Read-Host 'TELEGRAM_BOT_TOKEN'
  $token = $token.Trim()
  $bot = Validate-Token $token
}

if (-not $bot) {
  Block 'TOKEN_VALIDATION_FAILED. Create/regenerate a bot token in @BotFather and run this wizard again.'
  Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
  exit 2
}

Pass "Bot token valid: @$($bot.username)"

$chatId = $oldChatId
if (-not $chatId) { $chatId = Get-ChatId $token }

if (-not $chatId) {
  Write-Host ''
  Write-Host "Open Telegram, search @$($bot.username), press Start, then send any message like 'report'." -ForegroundColor Yellow
  Read-Host 'After sending a message to the bot, press Enter here'
  $chatId = Get-ChatId $token
}

if (-not $chatId) {
  Block 'CHAT_ID_DISCOVERY_FAILED. The bot has no received message yet. Send one message to the bot and rerun.'
  Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
  exit 3
}

Pass "Chat ID discovered: $chatId"
Write-NoBom $EnvTelegram "TELEGRAM_BOT_TOKEN=$token`nTELEGRAM_CHAT_ID=$chatId`n"
Pass ".env.telegram saved locally: $EnvTelegram"

$testOk = Send-Test $token $chatId
if (-not $testOk) {
  Block 'TOKEN_CHATID_PAIR_FAILED. Token is valid but chat id cannot receive messages.'
  Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
  exit 4
}
Pass 'Telegram test report sent.'

if (Test-Path $BridgePath) {
  Step 'Installing recurring Telegram report bridge task'
  powershell -ExecutionPolicy Bypass -File $BridgePath -InstallTask -IntervalMinutes $IntervalMinutes
}

Pass 'CHEONOK TELEGRAM CONNECT WIZARD COMPLETE'
Write-Host "REPORT_TASK: CHEONOK_TELEGRAM_REPORT_30M / every $IntervalMinutes minutes"
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
