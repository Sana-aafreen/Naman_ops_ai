@echo off
setlocal

cd /d "%~dp0..\Backend"
echo Starting backend from: %cd%
python main.py

endlocal

