# CHEONOK TikTok Social Signal Scout One-Step Runner
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\RUN_TIKTOK_SCOUT.ps1 "https://vt.tiktok.com/xxxx/"

param(
    [string]$Url = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Url)) {
    $Url = Read-Host "TikTok/Shorts/Reels URL 입력"
}

$Base = Join-Path $env:USERPROFILE "Desktop\CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Data = Join-Path $Base "data"
$Script = Join-Path $Tools "social_signal_scout.py"

Write-Host "[CHEONOK] Social Signal Scout 준비 중..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $Data | Out-Null

Write-Host "[1/4] 최신 scout script 다운로드" -ForegroundColor Cyan
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools/social_signal_scout.py" `
  -OutFile $Script

Write-Host "[2/4] Python/pip 확인 및 yt-dlp 설치" -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install --upgrade yt-dlp

Write-Host "[3/4] 링크 분석 실행" -ForegroundColor Cyan
python $Script $Url

Write-Host "[4/4] 최신 report.md 찾는 중" -ForegroundColor Cyan
$Latest = Get-ChildItem -Path (Join-Path $Data "social_signal_scout") -Filter "report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($Latest) {
    Write-Host "[DONE] Report:" $Latest.FullName -ForegroundColor Green
    notepad $Latest.FullName
} else {
    Write-Host "[WARN] report.md를 찾지 못했습니다. data 폴더를 확인하세요." -ForegroundColor Yellow
}
