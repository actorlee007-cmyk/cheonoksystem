# CHEONOK ONE CLICK SETUP
# ASCII only. Designed for minimum friction.
# Purpose:
# - One script installs/updates all CHEONOK social signal tools.
# - Creates one Start Here launcher for all workflows.
# - Fixes path issues with OneDrive/Korean Desktop paths.
# - Opens Telegram token setup only when needed.
#
# Usage:
# powershell -ExecutionPolicy Bypass -File CHEONOK_ONE_CLICK_SETUP.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Config = Join-Path $Base "config"
$Data = Join-Path $Base "data"
$Docs = Join-Path $Base "docs"
$Web = Join-Path $Base "web"
$TokenFile = Join-Path $Config "telegram_inbox_token.txt"
$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"
$RawDocs = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/docs"
$RawWeb = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/web"

function Write-Step($Text) { Write-Host $Text -ForegroundColor Cyan }
function Write-Ok($Text) { Write-Host $Text -ForegroundColor Green }
function Write-Warn($Text) { Write-Host $Text -ForegroundColor Yellow }

function Download-Tool($Name) {
    $Url = "$RawBase/$Name"
    $Out = Join-Path $Tools $Name
    Write-Host "  - $Name" -ForegroundColor DarkCyan
    Invoke-WebRequest -Uri $Url -OutFile $Out
}

function Download-Doc($Name) {
    $Url = "$RawDocs/$Name"
    $Out = Join-Path $Docs $Name
    Write-Host "  - docs/$Name" -ForegroundColor DarkCyan
    Invoke-WebRequest -Uri $Url -OutFile $Out
}

function Download-Web($Name) {
    $Url = "$RawWeb/$Name"
    $Out = Join-Path $Web $Name
    Write-Host "  - web/$Name" -ForegroundColor DarkCyan
    Invoke-WebRequest -Uri $Url -OutFile $Out
}

function Make-Bat($Name, $CommandText) {
    $Bat = Join-Path $Desktop $Name
    Set-Content -Path $Bat -Value $CommandText -Encoding ASCII
    return $Bat
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "CHEONOK ONE CLICK SETUP - UNIFIED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Desktop : $Desktop" -ForegroundColor Yellow
Write-Host "Base    : $Base" -ForegroundColor Yellow
Write-Host "Tools   : $Tools" -ForegroundColor Yellow
Write-Host "Config  : $Config" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green

New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Config | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null
New-Item -ItemType Directory -Force -Path $Docs | Out-Null
New-Item -ItemType Directory -Force -Path $Web | Out-Null

Write-Step "[1/6] Download latest CHEONOK tools"
$Files = @(
    "social_signal_scout_v02.py",
    "social_signal_scout_v03_analyze.py",
    "social_signal_scout_v04_db.py",
    "social_signal_universal_v01.py",
    "social_signal_input_gui.py",
    "social_signal_discovery_v05.py",
    "RUN_SOCIAL_DISCOVERY_SAFE.ps1",
    "cheonok_telegram_inbox.py",
    "START_CHEONOK_TELEGRAM_INBOX_SAFE.ps1",
    "cheonok_next_action_engine.py",
    "CHEONOK_CHANNEL_LEARNING_OS.ps1"
)
foreach ($F in $Files) { Download-Tool $F }

Write-Step "[2/6] Download docs/web assets"
try { Download-Doc "CHEONOK_SUBSCRIPTION_USER_GUIDE.md" } catch { Write-Warn "Guide doc download skipped" }
try { Download-Doc "CHEONOK_HOMEPAGE_CHATBOT_SPEC.md" } catch { Write-Warn "Chatbot spec download skipped" }
try { Download-Web "cheonok_chatbot_widget.html" } catch { Write-Warn "Chatbot widget download skipped" }

Write-Step "[3/6] Install/update dependencies"
python -m pip install --upgrade pip
python -m pip install --upgrade yt-dlp

Write-Step "[4/6] Create desktop launchers"
$InputBatText = "@echo off`r`ncd /d `"$Base`"`r`npython `"tools\social_signal_input_gui.py`"`r`npause`r`n"
$InputBat = Make-Bat "CHEONOK_SOCIAL_INPUT.bat" $InputBatText

$TelegramBatText = "@echo off`r`ncd /d `"$Base`"`r`npython `"tools\cheonok_telegram_inbox.py`"`r`npause`r`n"
$TelegramBat = Make-Bat "CHEONOK_TELEGRAM_INBOX.bat" $TelegramBatText

$DiscoveryBatText = "@echo off`r`ncd /d `"$Base`"`r`npowershell -ExecutionPolicy Bypass -File `"tools\RUN_SOCIAL_DISCOVERY_SAFE.ps1`"`r`npause`r`n"
$DiscoveryBat = Make-Bat "CHEONOK_DISCOVERY_RUN.bat" $DiscoveryBatText

$ChannelBatText = "@echo off`r`ncd /d `"$Base`"`r`npowershell -ExecutionPolicy Bypass -File `"tools\CHEONOK_CHANNEL_LEARNING_OS.ps1`"`r`npause`r`n"
$ChannelBat = Make-Bat "CHEONOK_CHANNEL_LEARNING.bat" $ChannelBatText

$NextActionBatText = "@echo off`r`ncd /d `"$Base`"`r`npython `"tools\cheonok_next_action_engine.py`"`r`nnotepad `"data\social_signal_scout\next_actions\latest_next_actions.md`"`r`npause`r`n"
$NextActionBat = Make-Bat "CHEONOK_NEXT_ACTION.bat" $NextActionBatText

$DocsBatText = "@echo off`r`ncd /d `"$Base`"`r`necho [1] Subscription User Guide`r`necho [2] Homepage Chatbot Spec`r`necho [3] Chatbot Widget HTML`r`necho.`r`nchoice /c 123 /m `"Select`"`r`nif errorlevel 3 notepad `"web\cheonok_chatbot_widget.html`"`r`nif errorlevel 2 notepad `"docs\CHEONOK_HOMEPAGE_CHATBOT_SPEC.md`"`r`nif errorlevel 1 notepad `"docs\CHEONOK_SUBSCRIPTION_USER_GUIDE.md`"`r`n"
$DocsBat = Make-Bat "CHEONOK_DOCS_AND_CHATBOT.bat" $DocsBatText

$StartHere = Join-Path $Desktop "CHEONOK_START_HERE.bat"
$StartHereText = "@echo off`r`n:menu`r`ncls`r`necho ============================================`r`necho CHEONOK START HERE`r`necho ============================================`r`necho [1] Link / SNS / Web one-shot analysis`r`necho [2] Teach a YouTube channel / playlist`r`necho [3] Find YouTube signal candidates automatically`r`necho [4] Phone Telegram Inbox`r`necho [5] Next Action Report`r`necho [6] Subscription guide / Homepage chatbot docs`r`necho [7] Exit`r`necho.`r`nchoice /c 1234567 /m `"Select`"`r`nif errorlevel 7 exit`r`nif errorlevel 6 start `"`" `"$DocsBat`" & goto menu`r`nif errorlevel 5 start `"`" `"$NextActionBat`" & goto menu`r`nif errorlevel 4 start `"`" `"$TelegramBat`" & goto menu`r`nif errorlevel 3 start `"`" `"$DiscoveryBat`" & goto menu`r`nif errorlevel 2 start `"`" `"$ChannelBat`" & goto menu`r`nif errorlevel 1 start `"`" `"$InputBat`" & goto menu`r`n"
Set-Content -Path $StartHere -Value $StartHereText -Encoding ASCII

Write-Ok "Created: $StartHere"
Write-Ok "Created: $InputBat"
Write-Ok "Created: $ChannelBat"
Write-Ok "Created: $DiscoveryBat"
Write-Ok "Created: $TelegramBat"
Write-Ok "Created: $NextActionBat"
Write-Ok "Created: $DocsBat"

Write-Step "[5/6] Telegram token readiness"
$Token = ""
if (Test-Path $TokenFile) { $Token = (Get-Content $TokenFile -Raw).Trim() }
if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Warn "Telegram token is not configured yet."
    Write-Warn "Phone workflow needs a Telegram bot token. PC/channel/discovery modes work without it."
    Write-Warn "Token file: $TokenFile"
    $SetupNow = Read-Host "Set Telegram token now? type Y or press Enter to skip"
    if ($SetupNow.Trim().ToUpper() -eq "Y") {
        Start-Process "https://t.me/BotFather"
        $Token = Read-Host "Paste Telegram bot token here"
        $Token = $Token.Trim()
        if (-not [string]::IsNullOrWhiteSpace($Token)) {
            Set-Content -Path $TokenFile -Value $Token -Encoding UTF8
            Write-Ok "Saved token to: $TokenFile"
        }
    }
} else {
    Write-Ok "Telegram token file exists: $TokenFile"
}

Write-Step "[6/6] Write unified quick guide"
$Guide = Join-Path $Desktop "CHEONOK_QUICK_GUIDE.txt"
$GuideText = @"
CHEONOK - QUICK GUIDE

Use only this first:
Double-click CHEONOK_START_HERE.bat

Menu:
1. Link / SNS / Web one-shot analysis
   Paste one link -> Analyze -> report generated.

2. Teach a YouTube channel / playlist
   Paste channel URL -> channel map -> top videos -> report.

3. Find YouTube signal candidates automatically
   System searches candidates and analyzes top items.

4. Phone Telegram Inbox
   Send link/photo/text from phone to Telegram bot.
   Requires token from @BotFather.

5. Next Action Report
   System reads latest reports and proposes what to do next.

6. Subscription guide / Homepage chatbot docs
   Open guide, chatbot spec, widget file.

Operating principle:
- Do not run individual Python files manually.
- Do not hunt paths.
- Start with CHEONOK_START_HERE.bat.
- If a workflow is separate, it must be added to Start Here.
- User chooses purpose, system handles files.

Status:
PAPER_ONLY TRUE.
LIVE_TRADE / CAPITAL_SCALE / KIS_ORDER_GATE BLOCKED.
"@
Set-Content -Path $Guide -Value $GuideText -Encoding UTF8
Write-Ok "Created: $Guide"

Start-Process $StartHere

Write-Host "============================================================" -ForegroundColor Green
Write-Host "DONE" -ForegroundColor Green
Write-Host "Use desktop file: CHEONOK_START_HERE.bat" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
pause
