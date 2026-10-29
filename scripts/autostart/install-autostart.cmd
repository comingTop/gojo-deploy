@echo off
REM Manual host test: run as the SAME Windows admin user who owns Epic/OBS.
REM Confirm console logon, no UAC prompts at next logon, and task history.
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-autostart.ps1"
if errorlevel 1 (echo Installation FAILED. & pause & exit /b 1)
echo Installed. Test at next console logon before allowing client use.
pause
