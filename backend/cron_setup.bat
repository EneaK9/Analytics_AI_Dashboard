@echo off
REM Setup Windows Task Scheduler for SKU Analysis
REM Run this as Administrator

echo 🕐 Setting up SKU Analysis Scheduled Task (Windows)...

REM Get current directory
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=python

REM Create scheduled task
echo 📝 Creating Windows scheduled task...

REM Delete existing task if it exists
schtasks /Delete /TN "SKU_Analysis_Cron" /F >nul 2>&1

REM Create new task (runs every 8 hours)
schtasks /Create /TN "SKU_Analysis_Cron" /TR "%PYTHON_PATH% %SCRIPT_DIR%sku_analysis_cron.py" /SC HOURLY /MO 8 /ST 00:00 /F

if %ERRORLEVEL% EQU 0 (
    echo ✅ Windows scheduled task created successfully!
    echo 📋 Task "SKU_Analysis_Cron" will run every 8 hours starting at midnight
) else (
    echo ❌ Failed to create scheduled task. Make sure you run this as Administrator.
    pause
    exit /b 1
)

echo.
echo 📊 Task details:
schtasks /Query /TN "SKU_Analysis_Cron" /V /FO LIST

echo.
echo 🔍 To check task status: schtasks /Query /TN "SKU_Analysis_Cron"
echo 🗑️ To remove task: schtasks /Delete /TN "SKU_Analysis_Cron" /F
echo ✅ Setup complete!

pause
