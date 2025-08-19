# Railway Deployment Guide

## 🚀 Quick Deploy

1. **Connect Repository**: Link `jaswantjat/finalboss-ID-` to Railway
2. **Auto-Deploy**: Railway will detect Dockerfile and deploy automatically
3. **Test**: Visit your Railway domain + `/health` to verify

## 🔧 PORT Environment Variable Solutions

### Problem
Railway injects a dynamic `PORT` environment variable, but Docker's JSON array form doesn't expand shell variables.

### ✅ Current Solution (Dockerfile)
Uses exec form with shell wrapper for proper variable expansion:
```dockerfile
CMD ["sh", "-c", "uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 🛡️ Alternative Solutions

#### Option 1: Entrypoint Script (Most Robust)
Replace `Dockerfile` with `Dockerfile.entrypoint`:
```bash
cp Dockerfile.entrypoint Dockerfile
```

#### Option 2: Python Launcher (Most Robust)
Use dedicated launcher script that reads PORT and passes integer to uvicorn:
```dockerfile
CMD ["python", "/app/run_server.py"]
```
Replace `Dockerfile` with `Dockerfile.python-launcher` for this approach.

#### Option 3: Railway Start Command Override
Let Railway handle the command via `railway.toml`:
```toml
[deploy]
startCommand = "uvicorn api_service:app --host 0.0.0.0 --port $PORT"
```

## 📋 Deployment Checklist

- ✅ **PORT Binding**: App listens on `0.0.0.0:$PORT`
- ✅ **Health Check**: `/health` endpoint returns 200
- ✅ **Dependencies**: All packages in requirements.txt
- ✅ **System Deps**: Tesseract + Spanish language pack
- ✅ **Docker Build**: No heredoc or parser errors

## 🧪 Local Testing

Test the Docker build locally:
```bash
# Build image
docker build -t fastapi-app .

# Run with custom port
docker run -p 8000:8000 -e PORT=8000 fastapi-app

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## 🔍 Troubleshooting

### "PORT is not a valid integer"
- **Cause**: Uvicorn receives literal "$PORT" string instead of integer
- **Fix**: Use `["sh", "-c", "..."]` for variable expansion or Python launcher script

### "unknown instruction: import"
- **Cause**: Docker heredoc in HEALTHCHECK
- **Fix**: Use inline Python or external script

### "tesseract not found"
- **Cause**: Missing system dependencies
- **Fix**: Dockerfile includes `tesseract-ocr tesseract-ocr-spa`

## 📚 API Endpoints

- `GET /` - API information
- `GET /health` - Health check (Railway monitoring)
- `GET /docs` - Interactive API documentation
- `POST /straighten` - Auto-rotate ID cards
- `POST /remove-background` - AI background removal
- `POST /convert-to-pdf` - Image to PDF conversion
