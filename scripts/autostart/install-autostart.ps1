# Manual test: interactive admin account, OBS imported, Python and Epic authenticated.
$ErrorActionPreference = 'Stop'

# Silent admin elevation so the Rockstar Games Launcher boots WITHOUT a UAC prompt
# during the hands-off session (the game cannot start unattended otherwise). This
# lowers UAC on this dedicated single-purpose gaming VM; it is a deliberate trade-off.
Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' `
    -Name ConsentPromptBehaviorAdmin -Value 0

# Ensure the portable AutoHotkey that start-session uses to auto-select STORY MODE.
$ahkExe = 'C:\gojo\tools\AutoHotkeyU64.exe'
if (-not (Test-Path $ahkExe)) {
    New-Item -ItemType Directory -Force 'C:\gojo\tools' | Out-Null
    $zip = Join-Path $env:TEMP 'ahk.zip'
    $ex  = Join-Path $env:TEMP 'ahkx'
    Invoke-WebRequest 'https://github.com/AutoHotkey/AutoHotkey/releases/download/v1.1.37.02/AutoHotkey_1.1.37.02.zip' `
        -UseBasicParsing -OutFile $zip
    Expand-Archive $zip $ex -Force
    Copy-Item (Join-Path $ex 'AutoHotkeyU64.exe') $ahkExe -Force
}
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$actions = @{
    'Gojo-Session' = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\gojo\autostart\start-session.ps1"'
    'Gojo-Orchestrator' = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c "C:\gojo\autostart\run-orchestrator.cmd"'
}
foreach ($name in $actions.Keys) {
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $name
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
    }
    Register-ScheduledTask -TaskName $name -Action $actions[$name] -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
}
# OBS is launched once by Gojo-Session after GTA, with --startvirtualcam.
# Do not add an independent OBS Startup shortcut: it races the scene/profile flags.
