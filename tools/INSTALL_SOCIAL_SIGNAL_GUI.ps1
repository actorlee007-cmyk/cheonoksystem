# CHEONOK Social Signal Scout GUI Installer
# ASCII only.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\INSTALL_SOCIAL_SIGNAL_GUI.ps1

$ErrorActionPreference = "Stop"

$Base = Join-Path $env:USERPROFILE "Desktop\CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Gui = Join-Path $Tools "social_signal_gui.py"
$Bat = Join-Path $env:USERPROFILE "Desktop\CHEONOK_SOCIAL_SCOUT_GUI.bat"
$RawGui = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_gui.py"

Write-Host "[CHEONOK GUI] INSTALL START" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null

Write-Host "[1/3] Download GUI" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawGui -OutFile $Gui

Write-Host "[2/3] Create desktop launcher" -ForegroundColor Cyan
$BatText = "@echo off`r`ncd /d %USERPROFILE%\Desktop\CHEONOK_SOCIAL_SCOUT`r`npython tools\social_signal_gui.py`r`npause`r`n"
Set-Content -Path $Bat -Value $BatText -Encoding ASCII

Write-Host "[3/3] Launch GUI" -ForegroundColor Cyan
Start-Process $Bat

Write-Host "[DONE] Desktop launcher created:" $Bat -ForegroundColor Green
