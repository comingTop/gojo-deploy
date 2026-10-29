@echo off
REM Manual host test: confirm GTA scripts path (Enhanced installs can differ).
REM Run only after merge to main. No config.local.json or credentials downloaded.
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy-autostart.ps1"
if errorlevel 1 (echo Deployment FAILED. & pause & exit /b 1)
echo Files deployed. Follow docs/remote-access-setup.md before installing tasks.
pause
