$ErrorActionPreference = "Continue"

$Root = "C:\CHEONOK\GLOBAL_HOMEPAGE_OS"
$Guard = Join-Path $Root "_SUPREME_AUTOPILOT_OS\legacy_guard"
$Report = Join-Path $Guard "LEGACY_REPORT_KILL_SWITCH_REPORT.txt"
$Log = Join-Path $Guard "legacy_task_scan.json"
$SupremePy = Join-Path $Root "_SUPREME_AUTOPILOT_OS\runtime\cheonok_supreme_autopilot.py"

New-Item -ItemType Directory -Force -Path $Guard | Out-Null

$legacyPatterns = @(
  "월 500만 원 부족분",
  "일 목표 부족분",
  "무료진단 제안: 0",
  "CEO 보고서 판매: 0",
  "CHEONOK 09:00 매시간 보고",
  "CHEONOK 10:00 매시간 보고",
  "CHEONOK 11:00 매시간 보고"
)

$scan = @()
$disabled = @()
$kept = @()

try {
  $tasks = Get-ScheduledTask | Where-Object {
    $_.TaskName -match "CHEONOK|cheonok|천옥|REPORT|Revenue|Autopilot|AUTO"
  }

  foreach ($t in $tasks) {
    $name = $t.TaskName
    $path = $t.TaskPath
    $actionText = ($t.Actions | ForEach-Object { ($_.Execute + " " + $_.Arguments) }) -join " | "
    $isSupreme = ($name -match "SUPREME|AUTOPILOT") -or ($actionText -match "supreme_autopilot|cheonok_supreme")
    $looksLegacy = ($actionText -match "hourly|report|telegram|revenue|python|powershell|CHEONOK") -and (-not $isSupreme)

    $entry = [ordered]@{
      task_name = $name
      task_path = $path
      action = $actionText
      is_supreme = $isSupreme
      looks_legacy = $looksLegacy
      result = "WATCH"
    }

    if ($looksLegacy) {
      try {
        Disable-ScheduledTask -TaskName $name -TaskPath $path | Out-Null
        $entry.result = "DISABLED_LEGACY_REPORT_TASK"
        $disabled += ($path + $name)
      } catch {
        $entry.result = "HOLD_DISABLE_FAILED"
      }
    } else {
      $entry.result = "KEPT"
      $kept += ($path + $name)
    }

    $scan += $entry
  }
} catch {
  $scan += [ordered]@{ error = $_.Exception.Message }
}

# Local file scan for legacy report generators
$legacyFiles = @()
try {
  if (Test-Path $Root) {
    Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Extension -in ".ps1", ".py", ".bat", ".txt", ".json" -and $_.Length -lt 2000000 } |
      ForEach-Object {
        try {
          $txt = Get-Content $_.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
          foreach ($p in $legacyPatterns) {
            if ($txt -like "*$p*") {
              $legacyFiles += [ordered]@{ file = $_.FullName; pattern = $p }
              break
            }
          }
        } catch {}
      }
  }
} catch {}

# Ensure Supreme local loop task exists
$ensureStatus = "HOLD_SUPREME_ENGINE_NOT_FOUND"
if (Test-Path $SupremePy) {
  try {
    $taskName = "CHEONOK_SUPREME_AUTOPILOT_LOOP"
    $tr = "`"python`" `"$SupremePy`""
    schtasks /Create /TN $taskName /SC MINUTE /MO 5 /TR $tr /F | Out-Null
    $ensureStatus = "PASS_SUPREME_LOOP_ENSURED_EVERY_5_MIN"
  } catch {
    $ensureStatus = "HOLD_SUPREME_LOOP_CREATE_FAILED"
  }
}

$result = [ordered]@{
  version = "CHEONOK_LEGACY_REPORT_KILL_SWITCH_001"
  executed_at = (Get-Date).ToString("s")
  root = $Root
  disabled_tasks = $disabled
  kept_tasks = $kept
  legacy_files = $legacyFiles
  supreme_loop_status = $ensureStatus
  canon = [ordered]@{
    final_goal = "1000억 시스템"
    monthly_attack_metric = "월 10억"
    old_monthly_5m_report = "BLOCK_LEGACY"
    zero_revenue = "CRITICAL"
    hold = "SAFE_BYPASS"
  }
}

$result | ConvertTo-Json -Depth 10 | Set-Content -Path $Log -Encoding UTF8

$text = @"
CHEONOK LEGACY REPORT KILL SWITCH 001

STATUS:
- Old monthly 5M report format: BLOCK_LEGACY
- Supreme target: 1000억 시스템
- Monthly attack metric: 월 10억
- Local supreme loop: $ensureStatus

DISABLED TASKS:
$($disabled -join "`r`n")

KEPT TASKS:
$($kept -join "`r`n")

LEGACY FILES FOUND:
$(($legacyFiles | ForEach-Object { $_.file + " :: " + $_.pattern }) -join "`r`n")

NEXT:
A. Reports must use SUPREME AUTOPILOT OS format.
B. Any report mentioning 월 500만 원 부족분 as top target is legacy and blocked.
C. Revenue 0 must generate execution queue, not passive advice.

CURRENT SYSTEM STATUS:
자율 학습 및 PAPER 데이터 축적 상태.
"@

Set-Content -Path $Report -Value $text -Encoding UTF8
Write-Host $text
