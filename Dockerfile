# Railway-friendly Dockerfile for FastAPI + OpenCV + Tesseract + Rembg
FROM python:3.11-slim

# Install system dependencies (OpenCV, Tesseract, fonts, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python deps first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (documentation only; Railway uses PORT env)
EXPOSE 8000

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Healthcheck uses app's /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python - <<'PY' || exit 1
import os, sys
import urllib.request
port = os.getenv('PORT', '8000')
url = f'http://127.0.0.1:{port}/health'
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY

# Start with Uvicorn bound to Railway's dynamic PORT
CMD ["bash", "-lc", "uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}"]

