# Setup OpenRGB Server Scheduled Task
# Run this script in an Elevated (Administrator) PowerShell window.

$ErrorActionPreference = "Stop"

# Check for Admin rights
$isAdmin = [bool]([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator! Please open PowerShell as Administrator and run it again."
    Exit 1
}

$taskName = "OpenRGB_Server"
$exePath = "C:\Program Files\OpenRGB\OpenRGB.exe"

if (-not (Test-Path $exePath)) {
    Write-Error "OpenRGB.exe not found at $exePath! Please ensure OpenRGB is installed there."
    Exit 1
}

Write-Host "Creating scheduled task '$taskName' to run OpenRGB server as Administrator at logon..."

$action = New-ScheduledTaskAction -Execute $exePath -Argument "--server"
$trigger = New-ScheduledTaskTrigger -AtLogon
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365)

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "Scheduled task created successfully!"
Write-Host "Starting the OpenRGB server task now..."
Start-ScheduledTask -TaskName $taskName

Write-Host "OpenRGB server is now running as Administrator in the background!"
Write-Host "Check port 6742 using: Get-NetTCPConnection -LocalPort 6742"
