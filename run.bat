@echo off
rem Daily pipeline: signals, briefs, decks, dashboard, then publish. Scheduled by Task Scheduler; safe to double-click.
cd /d "%~dp0"
python signals.py
python brief.py
python deck.py
python dashboard.py
git add -A
git commit -qm "refresh %date%"
git pull -q --rebase -X theirs origin main
git push -q origin main
