# Production-ready Dockerfile with staged dependency installation
FROM python:3.11-slim

# Environment variables for optimal Python and pip behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with error handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-spa \
    # OpenCV and graphics libraries
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libgfortran5 \
    # Additional utilities
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Upgrade pip and core build tools first
RUN python -m pip install --upgrade pip setuptools wheel

# Install dependencies in carefully ordered stages
# Stage 1: Core numerical and image processing
RUN pip install --no-cache-dir \
    numpy>=1.20.0 \
    pillow>=9.0.0 \
    opencv-python-headless>=4.5.0

# Stage 2: Web framework and basic tools
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    python-multipart>=0.0.6 \
    python-jose>=3.3.0 \
    pytesseract>=0.3.8 \
    reportlab>=4.0.0 \
    img2pdf>=0.4.4

# Stage 3: PyTorch (CPU version for better compatibility)
RUN pip install --no-cache-dir \
    torch>=1.11.0 \
    torchvision>=0.12.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Stage 4: ML and NLP libraries
RUN pip install --no-cache-dir \
    transformers>=4.20.0 \
    sentencepiece>=0.1.96 \
    onnxruntime>=1.12.0

# Stage 5: Background removal and OCR (most complex dependencies)
RUN pip install --no-cache-dir rembg>=2.0.67
RUN pip install --no-cache-dir paddleocr>=3.0.3

# Copy application code
COPY . .

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Simple healthcheck using curl-like approach with python
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,os,sys; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health', timeout=5); sys.exit(0)" || exit 1

# Start the FastAPI application (exec form with shell for proper env var expansion)
CMD ["sh", "-c", "uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}"]

