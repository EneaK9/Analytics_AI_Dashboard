@echo off
REM Setup Windows Task Scheduler for API Sync and SKU Analysis
REM Run this as Administrator

echo 🕐 Setting up API Sync and SKU Analysis Scheduled Tasks (Windows)...

REM Get current directory
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=python

REM Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

echo 📝 Creating Windows scheduled tasks...

REM Delete existing tasks if they exist
schtasks /Delete /TN "API_Sync_Cron" /F >nul 2>&1
schtasks /Delete /TN "SKU_Analysis_Cron" /F >nul 2>&1

REM Create API Sync task (checks every hour for 2-hour sync intervals - THE MAIN ONE!)
echo 🔄 Creating API Sync task (checks every hour for 2-hour intervals)...
schtasks /Create /TN "API_Sync_Cron" /TR "%PYTHON_PATH% %SCRIPT_DIR%api_sync_cron.py" /SC HOURLY /ST 00:00 /F

if %ERRORLEVEL% EQU 0 (
    echo ✅ API Sync scheduled task created successfully!
    echo 📋 Task "API_Sync_Cron" will check hourly for 2-hour sync intervals
) else (
    echo ❌ Failed to create API sync task. Make sure you run this as Administrator.
    pause
    exit /b 1
)

REM Create SKU Analysis task (runs every 2 hours)
echo 📊 Creating SKU Analysis task (every 2 hours)...
schtasks /Create /TN "SKU_Analysis_Cron" /TR "%PYTHON_PATH% %SCRIPT_DIR%sku_analysis_cron.py" /SC HOURLY /MO 2 /ST 01:00 /F

if %ERRORLEVEL% EQU 0 (
    echo ✅ SKU Analysis scheduled task created successfully!
    echo 📋 Task "SKU_Analysis_Cron" will run every 2 hours starting at 1:00 AM
) else (
    echo ❌ Failed to create SKU analysis task. Make sure you run this as Administrator.
    pause
    exit /b 1
)

echo.
echo 📊 Task details:
echo.
echo === API SYNC TASK (MAIN) ===
schtasks /Query /TN "API_Sync_Cron" /V /FO LIST
echo.
echo === SKU ANALYSIS TASK ===
schtasks /Query /TN "SKU_Analysis_Cron" /V /FO LIST

echo.
echo 🔍 Management commands:
echo   Check API sync status: schtasks /Query /TN "API_Sync_Cron"
echo   Check SKU analysis status: schtasks /Query /TN "SKU_Analysis_Cron"
echo   Remove API sync task: schtasks /Delete /TN "API_Sync_Cron" /F
echo   Remove SKU analysis task: schtasks /Delete /TN "SKU_Analysis_Cron" /F
echo.
echo 📁 Logs will be saved to: %SCRIPT_DIR%logs\
echo ✅ Setup complete!

pause
