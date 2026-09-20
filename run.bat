@echo off
cd /d "%~dp0"
python signals.py
python brief.py
python deck.py
python dashboard.py
start "" docs\index.html
