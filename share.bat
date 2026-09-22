@echo off
rem Starts the desk server (team mode, pushes to GitHub) and a Cloudflare Quick Tunnel.
rem The public URL is written to SHARE.md. Keep this window open; close it to stop sharing.
cd /d "%~dp0"
for /f "usebackq tokens=1,* delims==" %%a in (".desk.env") do set %%a=%%b
start "signal-desk server" /min cmd /c "python app.py --push > data\app.log 2>&1"
timeout /t 3 >nul
.tools\cloudflared.exe tunnel --url http://localhost:8787 --no-autoupdate 2> data\tunnel.log
