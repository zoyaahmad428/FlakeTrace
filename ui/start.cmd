@echo off
rem FlakeTrace web UI: backend on 127.0.0.1:8765 (new window), web app on http://127.0.0.1:5174
cd /d "%~dp0"
start "FlakeTrace backend" cmd /k py server.py
cd web
if not exist node_modules call npm install
call npm run dev
