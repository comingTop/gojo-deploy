@echo off
REM =====================================================================
REM  Deploy the latest Gojo AutoWalk.cs to GTA V and let SHVDN hot-reload.
REM  Just DOUBLE-CLICK this file on the AirGPU machine. It self-elevates
REM  (UAC prompt -> Yes) and overwrites the script. No typing required.
REM =====================================================================

REM --- self-elevate to admin (needed to write into Program Files) ---
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator rights...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

set "URL=https://raw.githubusercontent.com/comingTop/gojo-deploy/main/scripts/gta/AutoWalk.cs"
set "DEST=C:\Program Files\Epic Games\GTAV\scripts\AutoWalk.cs"

echo Downloading latest AutoWalk.cs ...
powershell -NoProfile -Command "try { Invoke-WebRequest '%URL%' -OutFile '%DEST%' -UseBasicParsing; Write-Host ('OK - ' + (Get-Item '%DEST%').Length + ' bytes written') -ForegroundColor Green } catch { Write-Host ('FAILED: ' + $_.Exception.Message) -ForegroundColor Red }"

echo.
echo Done. ScriptHookVDotNet should hot-reload AutoWalk.cs on the file change.
echo If Gojo still walks in place, press  Insert  in GTA to reload scripts.
echo.
pause
