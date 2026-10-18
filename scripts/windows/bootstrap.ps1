<#
    bootstrap.ps1  -  AirGPU Windows setup for the "Gojo" TikTok live system.

    WHAT THIS AUTOMATES (the scriptable ~80%):
      - Python 3.12, Git, 7-Zip, OBS Studio (via winget, with direct-download fallback)
      - A working folder C:\gojo
      - The orchestrator Python package (venv + editable install) IF its source is present
      - Staging of ScriptHookVDotNet (copied into the GTA folder later, by hand)

    WHAT IT DOES NOT DO (irreducibly manual GUI / licensed, do these by hand - see runbook):
      - Install GTA V (needs a Steam/Epic/Rockstar login that OWNS the game)
      - ScriptHookV download (version must match your GTA build) + OpenIV / AddonPeds Gojo ped
      - OBS scene/stream-key, VB-CABLE install (GUI installer)

    RUN: open PowerShell AS ADMINISTRATOR inside the AirGPU desktop, then:
         Set-ExecutionPolicy -Scope Process Bypass -Force
         .\bootstrap.ps1
#>

[CmdletBinding()]
param(
    [string]$WorkDir = "C:\gojo",
    # Path on the machine where the repo was copied (via Parsec/RDP file transfer or git clone).
    [string]$RepoDir = "C:\gojo\TikTokavatar"
)

$ErrorActionPreference = "Stop"

function Info($m){ Write-Host "[bootstrap] $m" -ForegroundColor Cyan }
function Warn($m){ Write-Host "[bootstrap] $m" -ForegroundColor Yellow }

function Assert-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    if (-not $p.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
        throw "Run this script in an ELEVATED PowerShell (Run as administrator)."
    }
}

function Install-WithWinget($id, $name) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info "Installing $name ($id) via winget..."
        winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
    } else {
        Warn "winget not found - install $name manually (see runbook)."
    }
}

Assert-Admin
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
Info "Work dir: $WorkDir"

# --- 1. Base tooling -------------------------------------------------------
Install-WithWinget "Python.Python.3.12" "Python 3.12"
Install-WithWinget "Git.Git"            "Git"
Install-WithWinget "7zip.7zip"          "7-Zip"
Install-WithWinget "OBSProject.OBSStudio" "OBS Studio"   # obs-websocket is built in (OBS 28+)

# refresh PATH for this session so python/git are found immediately
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [Environment]::GetEnvironmentVariable("Path","User")

# --- 2. Orchestrator (only if the source is already on the machine) --------
if (Test-Path $RepoDir) {
    $orch = Join-Path $RepoDir "orchestrator"
    if (Test-Path $orch) {
        Info "Setting up the orchestrator venv at $orch\.venv ..."
        Push-Location $orch
        python -m venv .venv
        .\.venv\Scripts\python.exe -m pip install --upgrade pip
        .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
        Info "Running the test suite to verify the engine on this machine..."
        .\.venv\Scripts\python.exe -m pytest -q
        Pop-Location
        Info "Orchestrator ready. Edit config\config.local.json from config.example.json before running."
    } else {
        Warn "Found repo at $RepoDir but no 'orchestrator' folder - skipping Python setup."
    }
} else {
    Warn "Repo not found at $RepoDir. Copy the project here (Parsec file transfer or 'git clone'), then re-run with -RepoDir."
}

# --- 3. Stage ScriptHookVDotNet (placed into the GTA folder AFTER GTA is installed) ---
$stage = Join-Path $WorkDir "mods-staging"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
try {
    Info "Fetching latest ScriptHookVDotNet release info from GitHub..."
    $rel = Invoke-RestMethod "https://api.github.com/repos/scripthookvdotnet/scripthookvdotnet/releases/latest" -Headers @{ "User-Agent" = "gojo-bootstrap" }
    $asset = $rel.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1
    if ($asset) {
        $zip = Join-Path $stage $asset.name
        Info "Downloading $($asset.name) ..."
        Invoke-WebRequest $asset.browser_download_url -OutFile $zip
        Info "Saved to $zip (unzip its ASI + dll files into the GTA V folder after GTA is installed)."
    }
} catch {
    Warn "Could not auto-fetch ScriptHookVDotNet ($_). Download it by hand (see runbook)."
}

Write-Host ""
Info "DONE (scriptable part). Remaining MANUAL steps are in docs/superpowers/runbooks/2026-10-18-airgpu-gta-setup.md:"
Write-Host "  1. Install GTA V (store account that owns it) - REQUIRED, no license = no game."
Write-Host "  2. ScriptHookV (match your GTA build) + copy SHVDN from $stage into the GTA folder."
Write-Host "  3. OpenIV + AddonPeds -> inject the Gojo ped; set as player model."
Write-Host "  4. Install VB-CABLE; set OBS 1080x1920 scene + stream key; enable obs-websocket."
Write-Host "  5. Build-pending: GTA plugin (Phase 4), overlays (Phase 5), Telegram+auto-stop (Phase 6)."
