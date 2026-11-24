@echo off
rem Start bot + Web UI with the project-local venv (http://localhost:5000)
rem Pure UIA automation: no process-memory read, no DB decryption, admin NOT required.
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py --web
pause
