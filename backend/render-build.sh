#!/bin/bash
set -o errexit  # Exit on error

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build completed successfully!" 