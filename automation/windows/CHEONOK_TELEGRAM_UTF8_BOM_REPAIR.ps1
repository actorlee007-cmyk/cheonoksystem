# CHEONOK TELEGRAM UTF8 BOM REPAIR
# Purpose:
# - Fix Korean mojibake in Windows PowerShell 5.1 by saving the local bridge script with UTF-8 BOM.
# - GitHub raw files are UTF-8, but Windows PowerShell 5.1 may parse UTF-8-without-BOM scripts as ANSI.
# - This installer is ASCII-only so it can run safely even under legacy PowerShell encoding.

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

function Step($m) { Write-Host "[CHEONOK] $m" -ForegroundColor Cyan }
function Pass($m) { Write-Host "[PASS] $m" -ForegroundColor Green }
function Block($m) { Write-Host "[BLOCK] $m" -ForegroundColor Yellow }
function Write-Utf8Bom($path, $text) {
  $utf8Bom = New-Object System.Text.UTF8Encoding($true)
  [System.IO.File]::WriteAllText($path, $text, $utf8Bom)
}
function Test-BridgeHasKorean($path) {
  try {
    $raw = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    return ($raw -match '정시 보고' -and $raw -match '매출 최우선')
  } catch { return $false }
}

New-Item -ItemType Directory -Force -Path $Root, $LogDir | Out-Null

Step 'Removing old Telegram report tasks'
try { Unregister-ScheduledTask -TaskName $TaskHourly -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}
try { Unregister-ScheduledTask -TaskName $TaskOld30 -Confirm:$false -ErrorAction SilentlyContinue | Out-Null } catch {}

Step 'Downloading bridge as UTF-8 text'
try {
  $wc = New-Object System.Net.WebClient
  $wc.Headers.Add('Cache-Control','no-cache')
  $wc.Encoding = [System.Text.Encoding]::UTF8
  $bridgeText = $wc.DownloadString($BridgeUrl + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
  Write-Utf8Bom $BridgePath $bridgeText
  Pass "Bridge saved with UTF-8 BOM: $BridgePath"
} catch {
  Block "Download/write failed: $($_.Exception.Message)"
  exit 1
}

if (-not (Test-BridgeHasKorean $BridgePath)) {
  Block 'Bridge Korean signature verification failed. Local file is still not valid UTF-8.'
  exit 2
}
Pass 'Bridge Korean signature verified'

Step 'Running bridge once and installing exact-hour task'
try {
  powershell -NoProfile -ExecutionPolicy Bypass -File $BridgePath -InstallTask -IntervalMinutes 60
} catch {
  Block "Bridge run failed: $($_.Exception.Message)"
  exit 3
}

Pass 'CHEONOK TELEGRAM UTF8 BOM REPAIR COMPLETE'
Write-Host "TASK: $TaskHourly / exact hour"
Write-Host 'EXPECTED: Korean report should no longer be mojibake.'
Write-Host 'FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE'
