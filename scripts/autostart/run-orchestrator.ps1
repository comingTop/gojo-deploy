# Manual host test required: python must resolve for the task's interactive user.
# Heartbeats show process liveness, NOT Telegram/TikTok/application readiness.
$ErrorActionPreference = 'Stop'
Set-Location 'C:\gojo\src\gojo-deploy-main\orchestrator'
$python = (Get-Command python.exe -ErrorAction Stop).Source
function Log($Message) { Add-Content C:\gojo\autostart.log "$(Get-Date -Format o) [orchestrator] $Message"; Write-Host $Message }
# This task is also triggered at logon: wait for the session task's GTA prerequisite.
$ready = $false
for ($i = 0; $i -lt 96; $i++) {
    try {
        $r = Invoke-WebRequest http://127.0.0.1:6721/health -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200 -and (Get-Process GTA5* -ErrorAction SilentlyContinue)) { $ready = $true; break }
    } catch { }
    Start-Sleep 5
}
if (-not $ready) { Log 'GTA readiness timeout; inspect free-roam/launcher'; exit 1 }
Start-Sleep 15
while ($true) {
    Log 'Starting python -m orchestrator'
    $p = Start-Process $python -ArgumentList '-u -m orchestrator' -NoNewWindow -PassThru
    while (-not $p.WaitForExit(30000)) { Log "heartbeat pid=$($p.Id)" }
    Log "Exited code=$($p.ExitCode); restart in 10 seconds"
    Start-Sleep 10
}
