@echo off
echo 🚀 Starting AI Dashboard in Production Mode (Windows)
echo 💻 Using Uvicorn with 4 workers (Gunicorn alternative for Windows)
echo.

cd /d "%~dp0"
python start_production.py

pause
