<#
.SYNOPSIS
    Installs (or uninstalls) the SpeedTestAgent as a Windows Scheduled Task
    that runs every 15 minutes.

.DESCRIPTION
    Run this script in an ELEVATED (Administrator) PowerShell prompt.

.PARAMETER Uninstall
    If specified, removes the scheduled task instead of creating it.
#>
param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$TaskName = "SpeedTestAgent"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$AgentScript = Join-Path $ScriptDir "speed_test_agent.py"

# --- Uninstall ---
if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Scheduled task '$TaskName' removed."
    } else {
        Write-Host "Scheduled task '$TaskName' not found. Nothing to remove."
    }
    return
}

# --- Pre-flight checks ---
if (-not (Test-Path $PythonExe)) {
    Write-Error @"
Python venv not found at: $PythonExe
Run these commands first:
    cd "$ScriptDir"
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
"@
    return
}

if (-not (Test-Path $AgentScript)) {
    Write-Error "Agent script not found at: $AgentScript"
    return
}

# --- Create the scheduled task ---
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$AgentScript`"" `
    -WorkingDirectory $ScriptDir

# Run every 15 minutes, indefinitely
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Run whether user is logged on or not; don't store password (run only when logged on)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

# Remove existing task if present
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Existing task '$TaskName' removed. Re-creating..."
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Runs speed test and traceroute every 15 minutes and logs results." `
    -RunLevel Limited

Write-Host ""
Write-Host "Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
Write-Host "  Runs every 15 minutes."
Write-Host "  Logs saved to: $(Join-Path $ScriptDir 'logs')"
Write-Host ""
Write-Host "To remove:  .\Install-Task.ps1 -Uninstall"
