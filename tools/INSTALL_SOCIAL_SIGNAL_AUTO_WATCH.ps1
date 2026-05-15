# CHEONOK Social Signal Auto Watch Installer
# ASCII only.
# Uses real Windows Desktop path, including OneDrive Desktop if configured.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\INSTALL_SOCIAL_SIGNAL_AUTO_WATCH.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$App = Join-Path $Tools "social_signal_auto_watch.py"
$Bat = Join-Path $Desktop "CHEONOK_SOCIAL_AUTO_WATCH.bat"
$RawApp = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_auto_watch.py"

Write-Host "[CHEONOK AUTO WATCH] INSTALL START" -ForegroundColor Green
Write-Host "Desktop:" $Desktop -ForegroundColor Yellow
Write-Host "Base:" $Base -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $Tools | Out-Null

Write-Host "[1/3] Download auto watch app" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawApp -OutFile $App

Write-Host "[2/3] Create desktop launcher" -ForegroundColor Cyan
$BatText = "@echo off`r`ncd /d `"$Base`"`r`npython tools\social_signal_auto_watch.py`r`npause`r`n"
Set-Content -Path $Bat -Value $BatText -Encoding ASCII

Write-Host "[3/3] Launch app" -ForegroundColor Cyan
Start-Process $Bat

Write-Host "[DONE] Desktop launcher created:" $Bat -ForegroundColor Green
