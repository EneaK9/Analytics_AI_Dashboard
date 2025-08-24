#!/bin/bash
# Setup Linux/Mac Cron Jobs for API Sync and SKU Analysis
# Run with: chmod +x cron_setup.sh && ./cron_setup.sh

echo "🕐 Setting up API Sync and SKU Analysis Cron Jobs (Linux/Mac)..."

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="python3"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

echo "📝 Setting up cron jobs..."

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing crontab (if any)
crontab -l 2>/dev/null > "$TEMP_CRON" || echo "# New crontab" > "$TEMP_CRON"

# Remove existing Analytics AI cron jobs
sed -i.bak '/# Analytics AI API Sync/d' "$TEMP_CRON"
sed -i.bak '/# Analytics AI SKU Analysis/d' "$TEMP_CRON"
sed -i.bak '/# Analytics AI Cache Refresh/d' "$TEMP_CRON"
sed -i.bak '/api_sync_cron.py/d' "$TEMP_CRON"
sed -i.bak '/sku_analysis_cron.py/d' "$TEMP_CRON"
sed -i.bak '/analytics_refresh_cron.py/d' "$TEMP_CRON"

# Add header comment
echo "" >> "$TEMP_CRON"
echo "# Analytics AI Dashboard Cron Jobs" >> "$TEMP_CRON"

# Add API Sync cron job (checks every hour for 2-hour sync intervals - THE MAIN ONE!)
echo "🔄 Adding API Sync cron job (checks hourly for 2-hour intervals)..."
echo "0 * * * * cd $SCRIPT_DIR && $PYTHON_PATH api_sync_cron.py >> $SCRIPT_DIR/logs/api_sync_cron.log 2>&1 # Analytics AI API Sync" >> "$TEMP_CRON"

# Add SKU Analysis cron job (runs every 2 hours)
echo "📊 Adding SKU Analysis cron job (every 2 hours)..."
echo "0 */2 * * * cd $SCRIPT_DIR && $PYTHON_PATH sku_analysis_cron.py >> $SCRIPT_DIR/logs/sku_analysis_cron.log 2>&1 # Analytics AI SKU Analysis" >> "$TEMP_CRON"

# Add Analytics Refresh cron job (runs every 5 minutes - TESTING)
echo "📈 Adding Analytics Refresh cron job (every 5 minutes - TESTING)..."
echo "*/5 * * * * cd $SCRIPT_DIR && $PYTHON_PATH analytics_refresh_cron.py >> $SCRIPT_DIR/logs/analytics_refresh_cron.log 2>&1 # Analytics AI Cache Refresh - TESTING" >> "$TEMP_CRON"

# Add log cleanup job (weekly)
echo "🧹 Adding log cleanup job (weekly)..."
echo "0 2 * * 0 find $SCRIPT_DIR/logs -name '*_cron.log.*' -mtime +30 -delete # Analytics AI Log Cleanup" >> "$TEMP_CRON"

# Install the new crontab
crontab "$TEMP_CRON"

if [ $? -eq 0 ]; then
    echo "✅ Cron jobs installed successfully!"
    echo ""
    echo "📋 Installed cron jobs:"
    echo "  🔄 API Sync: Hourly checks for 2-hour intervals (*:00)"
    echo "  📊 SKU Analysis: Every 2 hours (even hours: 00:00, 02:00, 04:00...)"
    echo "  🧹 Log Cleanup: Weekly on Sunday at 02:00"
    echo ""
    echo "📁 Logs will be saved to: $SCRIPT_DIR/logs/"
else
    echo "❌ Failed to install cron jobs"
    rm -f "$TEMP_CRON"
    exit 1
fi

# Cleanup
rm -f "$TEMP_CRON"

echo "📊 Current crontab:"
crontab -l | grep "Analytics AI"

echo ""
echo "🔍 Management commands:"
echo "  View crontab: crontab -l"
echo "  Edit crontab: crontab -e" 
echo "  View API sync logs: tail -f $SCRIPT_DIR/logs/api_sync_cron.log"
echo "  View SKU analysis logs: tail -f $SCRIPT_DIR/logs/sku_analysis_cron.log"
echo "  Test API sync now: cd $SCRIPT_DIR && $PYTHON_PATH api_sync_cron.py"
echo "  Test SKU analysis now: cd $SCRIPT_DIR && $PYTHON_PATH sku_analysis_cron.py"

echo ""
echo "✅ Setup complete!"