# Manual test: stop Gojo tasks/orchestrator/GTA before updating; confirm GTA path.
# Download every file to staging first. Existing files are backed up, never secrets.
param([string]$GtaScripts = 'C:\Program Files\Epic Games\GTAV\scripts')
$ErrorActionPreference = 'Stop'
$base = 'https://raw.githubusercontent.com/comingTop/gojo-deploy/main'
$stage = Join-Path $env:TEMP ([guid]::NewGuid().ToString())
New-Item -ItemType Directory $stage | Out-Null
$files = @{}
foreach ($name in @('start-session.ps1','run-orchestrator.cmd','run-orchestrator.ps1','install-autostart.cmd','install-autostart.ps1','deploy-autostart.cmd','deploy-autostart.ps1')) {
    $files["scripts/autostart/$name"] = "C:\gojo\autostart\$name"
}
$files['scripts/gta/AutoGojo.cs'] = "$GtaScripts\AutoGojo.cs"
$files['scripts/gta/AutoWalk.cs'] = "$GtaScripts\AutoWalk.cs"
$files['overlays/effect.html'] = 'C:\gojo\overlays\effect.html'
$files['obs/Gojo.json'] = 'C:\gojo\obs\Gojo.json'
$files['obs/profile.json'] = 'C:\gojo\obs\profile.json'
$files['obs/Gojo/basic.ini'] = 'C:\gojo\obs\Gojo\basic.ini'
$files['obs/README.md'] = 'C:\gojo\obs\README.md'
$files['docs/remote-access-setup.md'] = 'C:\gojo\remote-access-setup.md'
try {
    foreach ($src in $files.Keys) {
        $local = Join-Path $stage $src
        New-Item -ItemType Directory -Force (Split-Path $local) | Out-Null
        Invoke-WebRequest "$base/$src" -UseBasicParsing -OutFile $local
        if ((Get-Item $local).Length -eq 0) { throw "Empty download: $src" }
    }
    $backup = 'C:\gojo\backups\autostart-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
    foreach ($src in $files.Keys) {
        $dest = $files[$src]
        New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
        if (Test-Path $dest) {
            $saved = Join-Path $backup $src
            New-Item -ItemType Directory -Force (Split-Path $saved) | Out-Null
            Copy-Item $dest $saved
        }
        Copy-Item (Join-Path $stage $src) $dest -Force
        Write-Host "Deployed $dest"
    }
} finally { Remove-Item $stage -Recurse -Force }
