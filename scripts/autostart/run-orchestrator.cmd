@echo off
REM Run only via highest-privilege interactive Scheduled Task.
REM Manual test: Python path, runtime config, restart, heartbeat, Telegram powers.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\gojo\autostart\run-orchestrator.ps1"
exit /b %errorlevel%
