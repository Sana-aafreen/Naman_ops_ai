@echo off
setlocal enabledelayedexpansion

echo Stopping processes listening on port 8000...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8000" ^| findstr LISTENING') do (
  echo - taskkill /PID %%p /F
  taskkill /PID %%p /F >nul 2>nul
)

echo Done.
endlocal

