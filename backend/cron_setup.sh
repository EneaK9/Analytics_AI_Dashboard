#!/bin/bash
# Setup cron job for SKU Analysis (Linux/Unix)
# Run this script to install the cron job

echo "🕐 Setting up SKU Analysis Cron Job..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

# Create the cron job entry
CRON_JOB="0 */8 * * * cd $SCRIPT_DIR && $PYTHON_PATH sku_analysis_cron.py >> sku_analysis_cron.log 2>&1"

# Add to crontab if not already exists
if ! crontab -l 2>/dev/null | grep -q "sku_analysis_cron.py"; then
    echo "📝 Adding cron job to crontab..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added successfully!"
    echo "📋 Job will run every 8 hours: $CRON_JOB"
else
    echo "⚠️ Cron job already exists"
fi

echo ""
echo "📊 Current crontab:"
crontab -l

echo ""
echo "🔍 To check logs: tail -f $SCRIPT_DIR/sku_analysis_cron.log"
echo "🗑️ To remove cron job: crontab -e (then delete the line)"
echo "✅ Setup complete!"
