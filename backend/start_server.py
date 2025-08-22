#!/usr/bin/env python3
"""
Start FastAPI Server for AI Dashboard

Simple script to start the FastAPI server on the correct port.
"""

import uvicorn
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI server"""
    try:
        logger.info("🚀 Starting AI Dashboard FastAPI Server...")
        logger.info("📊 Server will be available at: http://localhost:8000")
        logger.info("📋 API docs available at: http://localhost:8000/docs")
        logger.info("🤖 Health check at: http://localhost:8000/health")
        
        # Import the FastAPI app
        from app import app
        
        # Start the server (single worker for development with hot reload)
        # Note: Multiple workers don't work with reload=True, so we use single worker for dev
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Failed to import app: {e}")
        logger.error("Make sure you're in the backend directory and dependencies are installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 