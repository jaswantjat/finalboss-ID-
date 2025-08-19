#!/bin/bash
# Docker entrypoint script for Railway deployment
# Handles PORT environment variable properly

set -e

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

echo "🚀 Starting FastAPI application on port $PORT"
echo "📡 Health check available at: http://0.0.0.0:$PORT/health"
echo "📚 API docs available at: http://0.0.0.0:$PORT/docs"

# Start uvicorn with proper port binding
exec uvicorn api_service:app --host 0.0.0.0 --port "$PORT" --log-level info
