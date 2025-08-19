#!/usr/bin/env python3
"""
Universal server launcher for Docker deployments
Handles PORT environment variable across all platforms (Railway, Heroku, etc.)
Ensures uvicorn receives integer port value, not string
"""
import os
import sys
import uvicorn

def get_port():
    """
    Get port from environment with multiple fallbacks
    Ensures we always return a valid integer
    """
    # Try multiple environment variable names
    port_sources = ["PORT", "API_PORT", "HTTP_PORT", "SERVER_PORT"]

    for env_var in port_sources:
        port_str = os.getenv(env_var)
        if port_str:
            try:
                port = int(port_str)
                if 1 <= port <= 65535:  # Valid port range
                    print(f"✅ Using port {port} from {env_var} environment variable")
                    return port
                else:
                    print(f"⚠️  Invalid port {port} from {env_var}, trying next...")
            except ValueError:
                print(f"⚠️  Non-integer port '{port_str}' from {env_var}, trying next...")

    # Default fallback
    default_port = 8000
    print(f"🔄 No valid PORT found, using default: {default_port}")
    return default_port

if __name__ == "__main__":
    try:
        port = get_port()

        print(f"🚀 Starting FastAPI server on 0.0.0.0:{port}")
        print(f"📡 Health check: http://0.0.0.0:{port}/health")
        print(f"📚 API docs: http://0.0.0.0:{port}/docs")
        print(f"🔧 Platform: {os.getenv('RAILWAY_ENVIRONMENT', 'Local')}")

        # Start uvicorn programmatically (guarantees integer port)
        uvicorn.run(
            "api_service:app",
            host="0.0.0.0",
            port=port,  # This is guaranteed to be an integer
            log_level="info",
            access_log=True,
            # Disable reload in production
            reload=False
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)
