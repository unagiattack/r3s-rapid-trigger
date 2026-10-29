@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m r3s_rt gui
) else (
  python -m r3s_rt gui
)
if errorlevel 1 pause
