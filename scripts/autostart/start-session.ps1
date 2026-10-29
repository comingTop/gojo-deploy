# Manual host test: Epic login, free-roam save, webhook semantics, OBS capture,
# and 5-8 minute boot target. A window/health response cannot prove free-roam
# or a non-black preview. Never automate LIVE Studio Go LIVE.
param([int]$TimeoutSeconds = 480, [int]$SettleSeconds = 15)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force C:\gojo | Out-Null
function Log($Message) { Add-Content C:\gojo\autostart.log "$(Get-Date -Format o) [session] $Message" }
try {
    Log 'Starting session; operator must verify preview before Go LIVE'
    if (-not (Get-Process GTA5* -ErrorAction SilentlyContinue)) {
        Start-Process 'com.epicgames.launcher://apps/9d2d0eb64d5c44529cece33fe2a46482?action=launch&silent=true'
        Log 'Epic launch requested'
    }
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        $gta = Get-Process GTA5* -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
        try {
            $r = Invoke-WebRequest http://127.0.0.1:6721/health -UseBasicParsing -TimeoutSec 3
            if ($gta -and $r.StatusCode -eq 200) { $ready = $true; break }
        } catch { } # mod not loaded yet; bounded wait below
        Start-Sleep 5
    }
    if (-not $ready) { throw 'GTA window/webhook timeout. Check launcher and free-roam save; no downstream startup.' }
    Log 'GTA window + webhook responding; waiting for model/mod settling'
    Start-Sleep $SettleSeconds
    Start-ScheduledTask -TaskName 'Gojo-Orchestrator'
    Log 'Orchestrator task requested (single-instance policy)'
    if (Get-Process obs64 -ErrorAction SilentlyContinue) {
        Log 'OBS already running: operator must confirm Virtual Camera, collection and profile manually'
    } else {
        $obs = 'C:\Program Files\obs-studio\bin\64bit\obs64.exe'
        Start-Process $obs -WorkingDirectory (Split-Path $obs) -ArgumentList '--collection "Gojo" --profile "Gojo" --startvirtualcam --disable-updater --minimize-to-tray'
        Log 'OBS launch requested with Virtual Camera; verify non-black preview manually'
    }
    Log 'Launch phases complete. Open LIVE Studio manually; Go LIVE remains manual.'
} catch { Log "FAILED: $_"; exit 1 }
