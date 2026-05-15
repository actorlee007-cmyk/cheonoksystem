# CHEONOK Social Signal Input GUI Installer
# ASCII only.
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\INSTALL_SOCIAL_SIGNAL_INPUT_GUI.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$App = Join-Path $Tools "social_signal_input_gui.py"
$Bat = Join-Path $Desktop "CHEONOK_SOCIAL_INPUT.bat"
$RawApp = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_input_gui.py"

Write-Host "[CHEONOK INPUT GUI] INSTALL START" -ForegroundColor Green
Write-Host "Desktop:" $Desktop -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $Tools | Out-Null

Write-Host "[1/3] Download input GUI" -ForegroundColor Cyan
Invoke-WebRequest -Uri $RawApp -OutFile $App

Write-Host "[2/3] Create desktop launcher" -ForegroundColor Cyan
$BatText = "@echo off`r`ncd /d `"$Base`"`r`npython tools\social_signal_input_gui.py`r`npause`r`n"
Set-Content -Path $Bat -Value $BatText -Encoding ASCII

Write-Host "[3/3] Launch input GUI" -ForegroundColor Cyan
Start-Process $Bat

Write-Host "[DONE] Desktop launcher created:" $Bat -ForegroundColor Green
