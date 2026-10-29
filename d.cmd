@echo off
REM =====================================================================
REM  Deploy ALL latest Gojo files from GitHub to the AirGPU machine.
REM  Double-click (self-elevates). No typing of long paths/URLs needed.
REM    - AutoWalk.cs            -> GTA scripts (SHVDN hot-reloads it)
REM    - reactions.json         -> orchestrator checkout (adds Tiny Diny)
REM    - __main__.py            -> orchestrator checkout (Telegram optional)
REM    - runtime_config.py      -> orchestrator checkout (idle default 180)
REM =====================================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator rights...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

set "BASE=https://raw.githubusercontent.com/comingTop/gojo-deploy/main"
set "ORCH=C:\gojo\src\gojo-deploy-main\orchestrator"
set "GTADIR=C:\Program Files\Epic Games\GTAV\scripts"

echo Deploying AutoWalk.cs ...
curl.exe -s -o "%GTADIR%\AutoWalk.cs"            "%BASE%/scripts/gta/AutoWalk.cs"
echo Deploying reactions.json ...
curl.exe -s -o "%ORCH%\config\reactions.json"    "%BASE%/orchestrator/config/reactions.json"
echo Deploying __main__.py ...
curl.exe -s -o "%ORCH%\orchestrator\__main__.py" "%BASE%/orchestrator/orchestrator/__main__.py"
echo Deploying runtime_config.py ...
curl.exe -s -o "%ORCH%\orchestrator\runtime_config.py" "%BASE%/orchestrator/orchestrator/runtime_config.py"

echo.
echo Done. Deployed:
powershell -NoProfile -Command "'%GTADIR%\AutoWalk.cs','%ORCH%\config\reactions.json','%ORCH%\orchestrator\__main__.py','%ORCH%\orchestrator\runtime_config.py' | %% { if (Test-Path $_) { Write-Host ('  OK  {0,8} bytes  {1}' -f (Get-Item $_).Length,$_) -ForegroundColor Green } else { Write-Host ('  MISSING  '+$_) -ForegroundColor Red } }"
echo.
echo SHVDN will hot-reload AutoWalk.cs; restart the orchestrator to pick up the rest.
pause
