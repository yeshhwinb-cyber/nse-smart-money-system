@echo off
setlocal
cd /d J:\sharekhan\nse-smart-money-system\backend
echo Starting NSE Smart Money Phase-1 Backend on http://127.0.0.1:8001
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
pause
