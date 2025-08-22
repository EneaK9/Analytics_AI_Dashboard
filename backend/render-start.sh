#!/bin/bash
set -o errexit  # Exit on error

echo "🚀 Starting Analytics AI Dashboard API..."

# Calculate optimal worker count (CPU cores * 2 + 1, max 4 for starter plan)
WORKERS=${WORKERS:-4}

echo "📊 Starting with $WORKERS workers for better concurrency..."

# Start the FastAPI server with Gunicorn + Uvicorn workers for production
exec gunicorn app:app \
    -w $WORKERS \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 