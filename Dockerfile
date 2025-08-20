# Full-featured production Dockerfile - Default build with all ML capabilities
FROM python:3.11-slim

# Environment variables for optimal Python and pip behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=3 \
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

# Install dependencies in optimized stages for full ML functionality
# Stage 1: Core foundation (numpy first - everything depends on it)
RUN pip install --no-cache-dir numpy>=1.20.0

# Stage 2: Image processing foundation
RUN pip install --no-cache-dir \
    pillow>=9.0.0 \
    opencv-python-headless>=4.5.0

# Stage 3: Web framework and utilities
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    python-multipart>=0.0.6 \
    python-jose>=3.3.0

# Stage 4: Document processing
RUN pip install --no-cache-dir \
    pytesseract>=0.3.8 \
    reportlab>=4.0.0 \
    img2pdf>=0.4.4

# Stage 5: PyTorch ecosystem (CPU-optimized for stability and size)
RUN pip install --no-cache-dir \
    torch>=1.11.0 \
    torchvision>=0.12.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Stage 6: NLP and transformers (after PyTorch)
RUN pip install --no-cache-dir \
    transformers>=4.20.0 \
    sentencepiece>=0.1.96

# Stage 7: ONNX Runtime (CPU version for compatibility)
RUN pip install --no-cache-dir onnxruntime>=1.12.0

# Stage 8: Background removal (depends on ONNX)
RUN pip install --no-cache-dir rembg>=2.0.67

# Stage 9: PaddleOCR (most complex - install last with retries)
RUN pip install --no-cache-dir paddleocr>=3.0.3 || \
    (echo "PaddleOCR install failed, retrying..." && sleep 10 && pip install --no-cache-dir paddleocr>=3.0.3) || \
    (echo "PaddleOCR install failed twice, retrying with --no-deps..." && pip install --no-cache-dir --no-deps paddleocr>=3.0.3)

# Copy application code
COPY . .

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Simple healthcheck using curl-like approach with python
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,os,sys; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health', timeout=5); sys.exit(0)" || exit 1

# Start the FastAPI application (exec form with shell for proper env var expansion)
CMD ["sh", "-c", "uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}"]

