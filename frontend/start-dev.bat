@echo off
REM ================================================
REM  VIZU Academy - Dev launcher
REM  Opens two windows: backend (FastAPI) + frontend (Next.js)
REM ================================================

start "VIZU Backend"  cmd /k "cd /d D:\VIZU-Academy\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

start "VIZU Frontend" cmd /k "cd /d D:\VIZU-Academy\frontend && npm run dev"
