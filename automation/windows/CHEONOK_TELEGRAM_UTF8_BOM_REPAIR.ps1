# CHEONOK TELEGRAM UTF8 BOM REPAIR v2
# ASCII-only installer for Windows PowerShell 5.1.
# Purpose:
# - Do not include Korean literals in this installer.
# - Download Telegram bridge as raw bytes.
# - Save local bridge with UTF-8 BOM so Windows PowerShell 5.1 parses Korean correctly.
# - Reinstall exact-hour Telegram report task.

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$Root = 'C:\CHEONOK'
$BridgePath = Join-Path $Root 'CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'
$BridgeUrl = 'https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/automation/windows/CHEONOK_TELEGRAM_REPORT_BRIDGE.ps1'
$LogDir = Join-Path $Root '_REPORT_LOGS'
$TaskHourly = 'CHEONOK_TELEGRAM_REPORT_HOURLY'
$TaskOld30 = 'CHEONOK_TELEGRAM_REPORT_30M'

function Step($m) { Write-Host ("[CHEONOK] " + $m) -ForegroundColor Cyan }
function Pass($m) { Write-Host ("[PASS] " + $m) -ForegroundColor Green }
function Block($m) { Write-Host ("[BLOCK] " + $m) -ForegroundColor Yellow }

function Write-BytesWithUtf8Bom($path, [byte[]]$bytes) {
  $hasBom = $false
  if ($bytes.Length -ge 3) {
    if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $hasBom = $true }
  }
  if ($hasBom) {
    [System.IO.File]::WriteAllBytes($path, $bytes)
  } else {
    $bom = [byte[]](0xEF, 0xBB, 0xBF)
    $out = New-Object byte[] ($bom.Length + $bytes.Length)
    [System.Array]::Copy($bom, 0, $out, 0, $bom.Length)
    [System.Array]::Copy($bytes, 0, $out, $bom.Length, $bytes.Length)
    [System.IO.File]::WriteAllBytes($path, $out)
  }
}

function Test-FileHasUtf8Bom($path) {
  if (-not (Test-Path $path)) { return $false }
  $fs = [System.IO.File]::OpenRead($path)
  try {
    if ($fs.Length -lt 3) { return $false }
    $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte(); $b2 = $fs.ReadByte()
    return ($b0 -eq 0xEF -and $b1 -eq 0xBB -and $b2 -eq 0xBF)
  } finally {
    $fs.Close()
  }
}

function Test-BridgeAsciiSignature($path) {
  if (-not (Test-Path $path)) { return $false }
  try {
    $raw = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    if ($raw -notmatch 'CHEONOK TELEGRAM REPORT BRIDGE v3') { return $false }
    if ($raw -notmatch 'charset=utf-8') { return $false }
    if ($raw -notmatch 'CHEONOK_TELEGRAM_REPORT_HOURLY') { return $false }
    return $true
  } catch {
    return $false
  }
}

New-Item -ItemType Directory -Force -Path $Root, $LogDir | Out-Null

Step 'Removing old Telegram report tasks'
try { Unregister-ScheduledTask -TaskName $TaskHourly -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}
try { Unregister-ScheduledTask -TaskName $TaskOld30 -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}

Step 'Downloading bridge as raw bytes'
try {
  $wc = New-Object System.Net.WebClient
  $wc.Headers.Add('Cache-Control','no-cache')
  $url = $BridgeUrl + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  $bytes = $wc.DownloadData($url)
  Write-BytesWithUtf8Bom $BridgePath $bytes
  Pass ("Bridge saved with UTF-8 BOM: " + $BridgePath)
} catch {
  Block ("Download/write failed: " + $_.Exception.Message)
  exit 1
}

if (-not (Test-FileHasUtf8Bom $BridgePath)) {
  Block 'Bridge does not have UTF-8 BOM.'
  exit 2
}
Pass 'Bridge BOM verified'

if (-not (Test-BridgeAsciiSignature $BridgePath)) {
  Block 'Bridge signature verification failed.'
  exit 3
}
Pass 'Bridge signature verified'

Step 'Running bridge once and installing exact-hour task'
try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $BridgePath -InstallTask -IntervalMinutes 60
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0 -and $null -ne $exitCode) {
    Block ("Bridge exited with code: " + $exitCode)
  }
} catch {
  Block ("Bridge run failed: " + $_.Exception.Message)
  exit 4
}

Pass 'CHEONOK TELEGRAM UTF8 BOM REPAIR COMPLETE'
Write-Host ("TASK: " + $TaskHourly + " / exact hour")
Write-Host 'EXPECTED: Korean report should no longer be mojibake.'
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
