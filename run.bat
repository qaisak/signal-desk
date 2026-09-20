@echo off
cd /d "%~dp0"
python signals.py
python dashboard.py
python decks.py
python dashboard.py
start "" dashboard.html
