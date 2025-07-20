#!/bin/bash
set -o errexit  # Exit on error

echo "🚀 Starting Analytics AI Dashboard API..."

# Start the FastAPI server with production settings
exec python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 