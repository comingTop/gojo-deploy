# Manual host test: Epic login, free-roam save, webhook semantics, OBS capture,
# and 5-8 minute boot target. A window/health response cannot prove free-roam
# or a non-black preview. Never automate LIVE Studio Go LIVE.
param([int]$TimeoutSeconds = 720, [int]$SettleSeconds = 15)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force C:\gojo | Out-Null
function Log($Message) { Add-Content C:\gojo\autostart.log "$(Get-Date -Format o) [session] $Message" }
try {
    Log 'Starting session; operator must verify preview before Go LIVE'
    $launchUri = 'com.epicgames.launcher://apps/9d2d0eb64d5c44529cece33fe2a46482?action=launch&silent=true'
    if (-not (Get-Process GTA5* -ErrorAction SilentlyContinue)) {
        # Cold boot: a launch URI fired before the Epic Launcher is up only starts Epic
        # and never reaches the game. Start Epic first, wait for it, then launch GTA.
        if (-not (Get-Process EpicGamesLauncher -ErrorAction SilentlyContinue)) {
            Start-Process 'com.epicgames.launcher://apps'
            Log 'Epic Games Launcher start requested'
            for ($e = 0; $e -lt 24 -and -not (Get-Process EpicGamesLauncher -ErrorAction SilentlyContinue); $e++) {
                Start-Sleep 5
            }
            Start-Sleep 20  # let Epic finish signing in before it will honour a launch URI
        }
        Start-Process $launchUri
        Log 'GTA launch requested'
    }
    # GTA always boots to the landing menu and waits for STORY MODE to be picked.
    # The AutoHotkey clicker selects it and exits itself once the in-game webhook
    # answers (free-roam reached), so it never interferes with gameplay. Requires the
    # ConsentPromptBehaviorAdmin=0 set by install-autostart so the Rockstar launcher
    # elevates without a UAC prompt.
    $ahkExe = 'C:\gojo\tools\AutoHotkeyU64.exe'
    $ahkScript = 'C:\gojo\autostart\gta-storymode.ahk'
    if ((Test-Path $ahkExe) -and (Test-Path $ahkScript)) {
        Start-Process $ahkExe -ArgumentList "`"$ahkScript`""
        Log 'STORY MODE auto-clicker (AutoHotkey) started'
    } else {
        Log 'AutoHotkey or gta-storymode.ahk missing; STORY MODE must be selected manually'
    }
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $ready = $false
    $i = 0
    while ((Get-Date) -lt $deadline) {
        $gta = Get-Process GTA5* -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
        try {
            $r = Invoke-WebRequest http://127.0.0.1:6721/health -UseBasicParsing -TimeoutSec 3
            if ($gta -and $r.StatusCode -eq 200) { $ready = $true; break }
        } catch { } # mod not loaded yet; bounded wait below
        # Cold boot: the first launch URI sometimes only wakes Epic. If GTA5 still has
        # not appeared after ~60s, re-issue the launch so Epic (now ready) opens the game.
        if (($i % 12 -eq 11) -and -not (Get-Process GTA5* -ErrorAction SilentlyContinue)) {
            Start-Process $launchUri
            Log 'GTA still absent; re-issued launch URI'
        }
        Start-Sleep 5
        $i++
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
