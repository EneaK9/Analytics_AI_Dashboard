#!/usr/bin/env python3
"""
Start FastAPI Server in Production Mode
Use this to test production setup locally with multiple workers
"""

import subprocess
import sys
import os
import platform
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI server in production mode with multiple workers"""
    try:
        is_windows = platform.system().lower() == "windows"
        
        logger.info("🚀 Starting AI Dashboard in PRODUCTION mode...")
        
        if is_windows:
            logger.info("💻 Windows detected - using Uvicorn with multiple workers")
            logger.info("ℹ️  Note: Gunicorn doesn't work on Windows, but production (Linux) will use Gunicorn")
            logger.info("📊 Using 4 workers for better concurrency")
            logger.info("📋 Server will be available at: http://localhost:8000")
            logger.info("🤖 Health check at: http://localhost:8000/health")
            
            # Use uvicorn with workers for Windows (limited but works)
            cmd = [
                "uvicorn", 
                "app:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--workers", "4",
                "--log-level", "info"
            ]
            
        else:
            logger.info("🐧 Linux/Unix detected - using Gunicorn with Uvicorn workers")
            logger.info("📊 Using 4 workers for better concurrency")  
            logger.info("📋 Server will be available at: http://localhost:8000")
            logger.info("🤖 Health check at: http://localhost:8000/health")
            
            # Use Gunicorn + Uvicorn workers for Linux/Unix
            cmd = [
                "gunicorn", 
                "app:app",
                "-w", "4",  # 4 workers
                "-k", "uvicorn.workers.UvicornWorker",
                "--bind", "0.0.0.0:8000",
                "--access-logfile", "-",
                "--error-logfile", "-", 
                "--log-level", "info",
                "--timeout", "120",
                "--keep-alive", "5"
            ]
        
        logger.info(f"🔧 Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except FileNotFoundError:
        logger.error("❌ Gunicorn not found. Install with: pip install gunicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
