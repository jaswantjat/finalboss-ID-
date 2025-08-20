# Production Dockerfile - Railway-optimized with proper ML dependencies
FROM python:3.11-slim

# Environment variables for stable server behavior
ENV PYTHONUNBUFFERED=1 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata \
    OMP_THREAD_LIMIT=1 \
    UVICORN_WORKERS=1 \
    DEBIAN_FRONTEND=noninteractive

# System deps: Tesseract + OSD + Spanish + OpenCV runtime libs + Paddle needs libgomp
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-osd tesseract-ocr-spa \
    libgl1 libglib2.0-0 libgomp1 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# (Optional) Bake rembg model to avoid cold downloads
RUN mkdir -p /root/.u2net && \
    curl -L -o /root/.u2net/u2net.onnx \
      https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

# Copy application code
COPY . .

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Simple healthcheck using curl-like approach with python
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,os,sys; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health', timeout=5); sys.exit(0)" || exit 1

CMD ["uvicorn","api_service:app","--host","0.0.0.0","--port","${PORT:-8080}","--workers","1"]

