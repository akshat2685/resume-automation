<#
.SYNOPSIS
    Registers the Portfolio Monitor Daemon as a Windows Scheduled Task (runs at user logon).

.DESCRIPTION
    Creates a scheduled task that runs monitor_daemon.py in the background at user logon.
    Runs with highest privileges, hidden window. Restarts on failure.
#>

param(
    [string]$AgentPath = "C:\Users\ijain\resume-automation\agent",
    [string]$TaskName = "PortfolioMonitorDaemon",
    [string]$Description = "Continuous monitoring daemon for GitHub, LinkedIn, Certificates, Local Repos. Pushes weekly update Saturday 8 PM IST."
)

# Path to python and script
$LocalVenvPython = Join-Path $AgentPath "..\.venv\Scripts\python.exe"
if (Test-Path $LocalVenvPython) {
    $PythonExe = (Resolve-Path $LocalVenvPython).Path
    Write-Host "Using virtual environment python: $PythonExe"
} else {
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $PythonCmd) {
        Write-Error "Python not found in PATH"
        exit 1
    }
    if ($PythonCmd -is [array]) {
        $PythonExe = $PythonCmd[0].Source
    } else {
        $PythonExe = $PythonCmd.Source
    }
}

$ScriptPath = Join-Path $AgentPath "monitor_daemon.py"
$WorkingDir = $AgentPath

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at: $PythonExe"
    exit 1
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found: $ScriptPath"
    exit 1
}

Write-Host "Registering task '$TaskName'..."
Write-Host "Python: $PythonExe"
Write-Host "Script: $ScriptPath"
Write-Host "Working Dir: $WorkingDir"

# Create action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $WorkingDir

# Trigger: At logon of any user
$Trigger = New-ScheduledTaskTrigger -AtLogon -RandomDelay 00:02:00

# Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 5) -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -Hidden -RunOnlyIfNetworkAvailable

# Principal: Current user, highest privileges
$Principal = New-ScheduledTaskPrincipal -UserId (whoami) -LogonType Interactive -RunLevel Highest

# Register task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $Description -Force
    Write-Host "✅ Task '$TaskName' registered successfully!" -ForegroundColor Green
    Write-Host "It will start automatically at next logon, or run manually with:"
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
} catch {
    Write-Error "Failed to register task: $_"
    exit 1
}

# Optional: Start immediately
$StartNow = Read-Host "Start the daemon now? (y/n)"
if ($StartNow -eq 'y') {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Daemon started. Check logs at: $AgentPath\daemon.log"
}