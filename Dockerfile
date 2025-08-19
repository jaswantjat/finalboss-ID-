# Railway-compatible Dockerfile for FastAPI + OpenCV + Tesseract + Rembg
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install essential system dependencies (minimal set for opencv-python-headless + tesseract)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Simple healthcheck using curl-like approach with python
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,os,sys; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health', timeout=5); sys.exit(0)" || exit 1

# Start the FastAPI application (shell form for env var expansion)
CMD uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}

