# Manual test: interactive admin account, OBS imported, Python and Epic authenticated.
$ErrorActionPreference = 'Stop'
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
