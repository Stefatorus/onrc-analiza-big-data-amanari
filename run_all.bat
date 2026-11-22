@echo off
rem Windows wrapper: rebuild everything (see run_all.py --list). Uses .venv if present.
setlocal
set "HERE=%~dp0"
if exist "%HERE%.venv\Scripts\python.exe" (set "PY=%HERE%.venv\Scripts\python.exe") else (set "PY=python")
"%PY%" -X utf8 "%HERE%run_all.py" %*
exit /b %ERRORLEVEL%
