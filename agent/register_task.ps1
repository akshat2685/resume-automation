# Register the Portfolio Monitor Daemon
$taskName = "PortfolioMonitorDaemon"
$actionScript = "C:\Users\ijain\Desktop\akshat\resume-automation\agent\run_daemon.bat"
$startupFolder = "C:\Users\ijain\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
$shortcutPath = Join-Path $startupFolder "PortfolioMonitorDaemon.lnk"

if (-not (Test-Path $actionScript)) {
    Write-Error "Action script not found at: $actionScript"
    exit 1
}

# Try registering via Task Scheduler first
Write-Host "Attempting to register task '$taskName' in Windows Task Scheduler..."
try {
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Task '$taskName' already exists in Task Scheduler. Unregistering existing task..."
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    }

    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$actionScript`""
    $trigger = New-ScheduledTaskTrigger -AtLogon
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Continuous background monitoring daemon for Akshat's Portfolio Updates." -ErrorAction Stop
    Write-Host "SUCCESS: Task registered successfully in Windows Task Scheduler."
    
    # Remove startup folder shortcut if it exists to avoid double running
    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
    }
    exit 0
} catch {
    Write-Warning "Could not register via Task Scheduler (often due to missing Admin permissions): $_"
}

# Fallback: Register in Windows Startup folder (requires no elevation/permissions)
Write-Host "Falling back to registering in the Windows User Startup folder..."
try {
    if (Test-Path $shortcutPath) {
        Write-Host "Startup shortcut already exists. Re-creating to ensure correct path..."
        Remove-Item $shortcutPath -Force
    }
    
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = $actionScript
    $Shortcut.WorkingDirectory = "C:\Users\ijain\Desktop\akshat\resume-automation"
    $Shortcut.WindowStyle = 7 # Minimized / Runs in background window
    $Shortcut.Save()
    
    Write-Host "SUCCESS: Shortcut created in User Startup folder: $shortcutPath"
    Write-Host "The daemon will start automatically whenever you log on to Windows."
} catch {
    Write-Error "Failed to register daemon in Startup folder: $_"
    exit 1
}
