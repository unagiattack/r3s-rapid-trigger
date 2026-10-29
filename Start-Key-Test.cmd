@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m r3s_rt key-test
) else (
  python -m r3s_rt key-test
)
if errorlevel 1 pause
