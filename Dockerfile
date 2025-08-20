# Production Dockerfile - Railway-optimized with proper ML dependencies
FROM python:3.11-slim

# Environment variables for stable server behavior
ENV PYTHONUNBUFFERED=1 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata \
    OMP_THREAD_LIMIT=1 \
    UVICORN_WORKERS=1 \
    DEBIAN_FRONTEND=noninteractive

# System deps: Build tools + Image libraries + Tesseract + Runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies for Python packages
    build-essential \
    gcc \
    g++ \
    python3-dev \
    pkg-config \
    # Image processing libraries (required for Pillow)
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff5-dev \
    libfreetype6-dev \
    # Math libraries (required for numpy)
    libblas-dev \
    liblapack-dev \
    gfortran \
    # Tesseract OCR
    tesseract-ocr tesseract-ocr-osd tesseract-ocr-spa \
    # Runtime libraries
    libgl1 libglib2.0-0 libgomp1 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Install dependencies in stages for better error handling
# Stage 1: Core dependencies
RUN pip install --no-cache-dir \
    numpy>=1.20.0,<2.0.0 \
    Pillow>=9.0.0,<11.0.0

# Stage 2: Web framework
RUN pip install --no-cache-dir \
    fastapi>=0.104.0,<1.0.0 \
    uvicorn>=0.24.0,<1.0.0 \
    python-multipart>=0.0.6 \
    python-jose>=3.3.0

# Stage 3: Image processing
RUN pip install --no-cache-dir \
    opencv-python-headless>=4.8.0,<5.0.0 \
    pytesseract>=0.3.8

# Stage 4: Document processing
RUN pip install --no-cache-dir \
    reportlab>=4.0.0,<5.0.0 \
    img2pdf>=0.4.4

# Stage 5: ONNX and background removal
RUN pip install --no-cache-dir \
    onnxruntime>=1.12.0,<2.0.0 \
    rembg>=2.0.50,<3.0.0

# Stage 6: PaddlePaddle (install first)
RUN pip install --no-cache-dir paddlepaddle>=2.5.0,<3.0.0

# Stage 7: PaddleOCR (install after PaddlePaddle)
RUN pip install --no-cache-dir paddleocr>=2.7.0,<3.0.0

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

