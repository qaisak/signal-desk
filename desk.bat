@echo off
rem Opens the desk locally (no password). Add account / request brief / refresh work instantly.
cd /d "%~dp0"
python app.py --open --push
