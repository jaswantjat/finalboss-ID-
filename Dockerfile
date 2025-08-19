# Railway-friendly Dockerfile for FastAPI + OpenCV + Tesseract + Rembg
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps: Tesseract + Spanish data + libs for Pillow/OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-spa libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Add the healthcheck script
COPY docker/healthcheck.py /healthcheck.py

# Expose (metadata only; Railway relies on PORT env)
EXPOSE 8000

# Robust healthcheck (no heredoc)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD ["python", "/healthcheck.py"]

# Start the API
CMD ["python", "api_service.py"]

