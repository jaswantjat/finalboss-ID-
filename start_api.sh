#!/bin/bash
# Start the ID Card Straightening API Service

echo "🚀 Starting ID Card Straightening API Service"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "id_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv id_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source id_env/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if tesseract is available
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Warning: Tesseract OCR not found!"
    echo "   Please install tesseract:"
    echo "   - macOS: brew install tesseract"
    echo "   - Ubuntu: sudo apt-get install tesseract-ocr"
    echo "   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi

echo ""
echo "🌐 Starting API server..."
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔗 API Base URL: http://localhost:8000"
echo "❤️  Health Check: http://localhost:8000/health"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo "=============================================="

# Start the API server
python3 api_service.py
