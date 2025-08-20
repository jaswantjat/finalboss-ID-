# Production Dockerfile - Full ML capabilities with robust package management
FROM python:3.11-slim-bookworm

# Environment variables for optimal Python and pip behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=3 \
    DEBIAN_FRONTEND=noninteractive

# Update package lists first
RUN apt-get update && apt-get upgrade -y

# Install system dependencies in small, reliable groups
# Group 1: Essential utilities (always available)
RUN apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

# Group 2: Build tools (required for Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

# Group 3: Tesseract OCR (core functionality)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

# Group 4: Tesseract language packs (with individual error handling)
RUN apt-get update && \
    (apt-get install -y --no-install-recommends tesseract-ocr-eng || echo "English pack not available") && \
    (apt-get install -y --no-install-recommends tesseract-ocr-spa || echo "Spanish pack not available") && \
    (apt-get install -y --no-install-recommends tesseract-ocr-osd || echo "OSD pack not available") && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Group 5: Graphics libraries (with fallbacks)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libglib2.0-0 && \
    (apt-get install -y --no-install-recommends libsm6 || echo "libsm6 not available") && \
    (apt-get install -y --no-install-recommends libxext6 || echo "libxext6 not available") && \
    (apt-get install -y --no-install-recommends libxrender-dev || echo "libxrender-dev not available") && \
    (apt-get install -y --no-install-recommends libgomp1 || echo "libgomp1 not available") && \
    (apt-get install -y --no-install-recommends libgfortran5 || echo "libgfortran5 not available") && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Group 6: OpenGL libraries (multiple fallbacks)
RUN apt-get update && \
    (apt-get install -y --no-install-recommends libgl1-mesa-glx || \
     apt-get install -y --no-install-recommends libgl1-mesa-dev || \
     apt-get install -y --no-install-recommends libgl1 || \
     echo "OpenGL libraries not available") && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

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

