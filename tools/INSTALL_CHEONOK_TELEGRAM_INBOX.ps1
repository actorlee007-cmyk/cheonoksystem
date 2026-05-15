# CHEONOK Telegram Inbox Installer
# ASCII only.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\INSTALL_CHEONOK_TELEGRAM_INBOX.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Config = Join-Path $Base "config"
$Runner = Join-Path $Tools "cheonok_telegram_inbox.py"
$Bat = Join-Path $Desktop "CHEONOK_TELEGRAM_INBOX.bat"
$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"

Write-Host "[CHEONOK TELEGRAM INBOX] INSTALL START" -ForegroundColor Green
Write-Host "Desktop:" $Desktop -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Config | Out-Null

Write-Host "[1/4] Download inbox and required scripts" -ForegroundColor Cyan
Invoke-WebRequest -Uri "$RawBase/cheonok_telegram_inbox.py" -OutFile $Runner
Invoke-WebRequest -Uri "$RawBase/social_signal_universal_v01.py" -OutFile (Join-Path $Tools "social_signal_universal_v01.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v02.py" -OutFile (Join-Path $Tools "social_signal_scout_v02.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v03_analyze.py" -OutFile (Join-Path $Tools "social_signal_scout_v03_analyze.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v04_db.py" -OutFile (Join-Path $Tools "social_signal_scout_v04_db.py")

Write-Host "[2/4] Install/update dependency" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/4] Create desktop launcher" -ForegroundColor Cyan
$BatText = "@echo off`r`ncd /d `"$Base`"`r`npython tools\cheonok_telegram_inbox.py`r`npause`r`n"
Set-Content -Path $Bat -Value $BatText -Encoding ASCII

Write-Host "[4/4] Token setup reminder" -ForegroundColor Cyan
Write-Host "Put Telegram bot token here:" (Join-Path $Config "telegram_inbox_token.txt") -ForegroundColor Yellow
Write-Host "Then run desktop launcher:" $Bat -ForegroundColor Yellow

Write-Host "[DONE]" -ForegroundColor Green
