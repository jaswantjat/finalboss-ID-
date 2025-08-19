#!/usr/bin/env python3
"""
Railway-compatible server launcher
Reads PORT environment variable and starts Uvicorn programmatically
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment with fallbacks
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    
    print(f"🚀 Starting FastAPI server on 0.0.0.0:{port}")
    print(f"📡 Health check: http://0.0.0.0:{port}/health")
    print(f"📚 API docs: http://0.0.0.0:{port}/docs")
    
    # Start uvicorn programmatically (passes integer port directly)
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
