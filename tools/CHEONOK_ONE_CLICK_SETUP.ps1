# CHEONOK ONE CLICK SETUP
# ASCII only. Designed for minimum friction.
# Purpose:
# - One script installs/updates all CHEONOK social signal tools.
# - Creates desktop launchers.
# - Fixes path issues with OneDrive/Korean Desktop paths.
# - Opens Telegram token setup only when needed.
#
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\CHEONOK_ONE_CLICK_SETUP.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Config = Join-Path $Base "config"
$Data = Join-Path $Base "data"
$TokenFile = Join-Path $Config "telegram_inbox_token.txt"
$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"

function Write-Step($Text) {
    Write-Host $Text -ForegroundColor Cyan
}

function Write-Ok($Text) {
    Write-Host $Text -ForegroundColor Green
}

function Write-Warn($Text) {
    Write-Host $Text -ForegroundColor Yellow
}

function Download-Tool($Name) {
    $Url = "$RawBase/$Name"
    $Out = Join-Path $Tools $Name
    Write-Host "  - $Name" -ForegroundColor DarkCyan
    Invoke-WebRequest -Uri $Url -OutFile $Out
}

function Make-Bat($Name, $PythonScript) {
    $Bat = Join-Path $Desktop $Name
    $BatText = "@echo off`r`ncd /d `"$Base`"`r`npython `"$PythonScript`"`r`npause`r`n"
    Set-Content -Path $Bat -Value $BatText -Encoding ASCII
    return $Bat
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "CHEONOK ONE CLICK SETUP" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Desktop : $Desktop" -ForegroundColor Yellow
Write-Host "Base    : $Base" -ForegroundColor Yellow
Write-Host "Tools   : $Tools" -ForegroundColor Yellow
Write-Host "Config  : $Config" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green

New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Config | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null

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
    "START_CHEONOK_TELEGRAM_INBOX_SAFE.ps1"
)
foreach ($F in $Files) { Download-Tool $F }

Write-Step "[2/6] Install/update dependencies"
python -m pip install --upgrade pip
python -m pip install --upgrade yt-dlp

Write-Step "[3/6] Create desktop launchers"
$InputBat = Make-Bat "CHEONOK_SOCIAL_INPUT.bat" "tools\social_signal_input_gui.py"
$TelegramBat = Make-Bat "CHEONOK_TELEGRAM_INBOX.bat" "tools\cheonok_telegram_inbox.py"
$DiscoveryBat = Join-Path $Desktop "CHEONOK_DISCOVERY_RUN.bat"
$DiscoveryBatText = "@echo off`r`ncd /d `"$Base`"`r`npowershell -ExecutionPolicy Bypass -File `"tools\RUN_SOCIAL_DISCOVERY_SAFE.ps1`"`r`npause`r`n"
Set-Content -Path $DiscoveryBat -Value $DiscoveryBatText -Encoding ASCII

$StartHere = Join-Path $Desktop "CHEONOK_START_HERE.bat"
$StartHereText = "@echo off`r`necho [1] PC link input GUI`r`necho [2] Telegram phone inbox`r`necho [3] YouTube discovery scout`r`necho.`r`nchoice /c 123 /m `"Select`"`r`nif errorlevel 3 start `"`" `"$DiscoveryBat`"`r`nif errorlevel 2 start `"`" `"$TelegramBat`"`r`nif errorlevel 1 start `"`" `"$InputBat`"`r`n"
Set-Content -Path $StartHere -Value $StartHereText -Encoding ASCII

Write-Ok "Created: $InputBat"
Write-Ok "Created: $TelegramBat"
Write-Ok "Created: $DiscoveryBat"
Write-Ok "Created: $StartHere"

Write-Step "[4/6] Telegram token readiness"
$Token = ""
if (Test-Path $TokenFile) {
    $Token = (Get-Content $TokenFile -Raw).Trim()
}
if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Warn "Telegram token is not configured yet."
    Write-Warn "Phone workflow needs a Telegram bot token. PC link input works without it."
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

Write-Step "[5/6] Write quick guide"
$Guide = Join-Path $Desktop "CHEONOK_SOCIAL_QUICK_GUIDE.txt"
$GuideText = @"
CHEONOK SOCIAL SIGNAL - QUICK GUIDE

1. PC easiest mode
   Double-click: CHEONOK_SOCIAL_INPUT.bat
   Paste link -> Analyze -> ChatGPT brief copied.

2. Phone mode
   First create Telegram bot token from @BotFather.
   Save token here:
   $TokenFile
   Then double-click: CHEONOK_TELEGRAM_INBOX.bat
   Keep black window open.
   On phone: share link/photo/text to your Telegram bot.

3. Discovery mode
   Double-click: CHEONOK_DISCOVERY_RUN.bat
   It searches YouTube candidates and analyzes top items.

4. Start menu
   Double-click: CHEONOK_START_HERE.bat

Status principle:
- One action first.
- No file hunting.
- No repeated manual path work.
- If a step requires more than one decision, it must be turned into a launcher.
"@
Set-Content -Path $Guide -Value $GuideText -Encoding UTF8
Write-Ok "Created: $Guide"

Write-Step "[6/6] Launch PC input GUI now"
Start-Process $InputBat

Write-Host "============================================================" -ForegroundColor Green
Write-Host "DONE" -ForegroundColor Green
Write-Host "Use desktop file: CHEONOK_START_HERE.bat" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
pause
