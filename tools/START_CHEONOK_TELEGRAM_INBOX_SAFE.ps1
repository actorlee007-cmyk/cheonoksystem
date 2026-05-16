# CHEONOK Telegram Inbox SAFE Starter
# ASCII only.
# Purpose:
# - Download latest Telegram Inbox scripts
# - Ensure config folder exists
# - Ask for token if missing
# - Validate token through Telegram getMe
# - Start inbox runner

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Config = Join-Path $Base "config"
$TokenFile = Join-Path $Config "telegram_inbox_token.txt"
$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"

Write-Host "[CHEONOK TELEGRAM INBOX SAFE START]" -ForegroundColor Green
Write-Host "Desktop:" $Desktop -ForegroundColor Yellow
Write-Host "Base:" $Base -ForegroundColor Yellow
Write-Host "TokenFile:" $TokenFile -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Config | Out-Null

Write-Host "[1/5] Download latest scripts" -ForegroundColor Cyan
Invoke-WebRequest -Uri "$RawBase/cheonok_telegram_inbox.py" -OutFile (Join-Path $Tools "cheonok_telegram_inbox.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_universal_v01.py" -OutFile (Join-Path $Tools "social_signal_universal_v01.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v02.py" -OutFile (Join-Path $Tools "social_signal_scout_v02.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v03_analyze.py" -OutFile (Join-Path $Tools "social_signal_scout_v03_analyze.py")
Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v04_db.py" -OutFile (Join-Path $Tools "social_signal_scout_v04_db.py")

Write-Host "[2/5] Install/update dependency" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[3/5] Check token" -ForegroundColor Cyan
$Token = ""
if (Test-Path $TokenFile) {
    $Token = (Get-Content $TokenFile -Raw).Trim()
}

if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Host "Telegram bot token is missing." -ForegroundColor Yellow
    Write-Host "Open Telegram -> @BotFather -> /newbot -> copy token." -ForegroundColor Yellow
    Start-Process "https://t.me/BotFather"
    $Token = Read-Host "Paste Telegram bot token here"
    $Token = $Token.Trim()
    if ([string]::IsNullOrWhiteSpace($Token)) {
        Write-Host "[ERROR] Token empty. Stop." -ForegroundColor Red
        pause
        exit 1
    }
    Set-Content -Path $TokenFile -Value $Token -Encoding UTF8
    Write-Host "Saved token to:" $TokenFile -ForegroundColor Green
}

Write-Host "[4/5] Validate token" -ForegroundColor Cyan
$MeUrl = "https://api.telegram.org/bot$Token/getMe"
try {
    $Me = Invoke-RestMethod -Uri $MeUrl -Method Get
    if ($Me.ok -ne $true) {
        throw "Telegram getMe returned not ok"
    }
    Write-Host "Bot validated:" ("@" + $Me.result.username) -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Token validation failed." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Edit token file:" $TokenFile -ForegroundColor Yellow
    notepad $TokenFile
    pause
    exit 1
}

Write-Host "[5/5] Start inbox runner" -ForegroundColor Cyan
Write-Host "Keep this window open. Send link/photo/text to your bot from phone." -ForegroundColor Yellow
Set-Location -LiteralPath $Base
python "tools\cheonok_telegram_inbox.py"
pause
