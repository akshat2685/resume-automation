@echo off
cd /d "%~dp0"
echo Starting Portfolio Monitor Daemon...
echo Logs will be written to daemon.log
echo Press Ctrl+C to stop
echo.
python monitor_daemon.py
pause