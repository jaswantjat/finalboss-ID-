#!/bin/bash
# Test pip install process to identify specific package conflicts

set -e

echo "🧪 Testing pip install process..."

# Create a temporary test environment
echo "📦 Creating test environment..."
docker run --rm -v $(pwd):/app -w /app python:3.11-slim bash -c "
    echo '🔧 Upgrading pip...'
    pip install --upgrade pip setuptools wheel
    
    echo '📋 Testing core dependencies...'
    pip install --no-cache-dir numpy>=1.20.0,<2.0.0 Pillow>=9.0.0,<11.0.0 || exit 1
    
    echo '🌐 Testing web framework...'
    pip install --no-cache-dir fastapi>=0.104.0,<1.0.0 uvicorn>=0.24.0,<1.0.0 python-multipart>=0.0.6 python-jose>=3.3.0 || exit 2
    
    echo '📷 Testing image processing...'
    pip install --no-cache-dir opencv-python-headless>=4.8.0,<5.0.0 pytesseract>=0.3.8 || exit 3
    
    echo '📄 Testing document processing...'
    pip install --no-cache-dir reportlab>=4.0.0,<5.0.0 img2pdf>=0.4.4 || exit 4
    
    echo '🤖 Testing ONNX and background removal...'
    pip install --no-cache-dir onnxruntime>=1.12.0,<2.0.0 rembg>=2.0.50,<3.0.0 || exit 5
    
    echo '🧠 Testing PaddlePaddle...'
    pip install --no-cache-dir paddlepaddle>=2.5.0,<3.0.0 || exit 6
    
    echo '🔍 Testing PaddleOCR...'
    pip install --no-cache-dir paddleocr>=2.7.0,<3.0.0 || exit 7
    
    echo '✅ All packages installed successfully!'
    
    echo '📊 Package versions:'
    python -c \"
import numpy, PIL, cv2, fastapi, uvicorn
print(f'numpy: {numpy.__version__}')
print(f'Pillow: {PIL.__version__}')
print(f'OpenCV: {cv2.__version__}')
print(f'FastAPI: {fastapi.__version__}')
print(f'Uvicorn: {uvicorn.__version__}')
try:
    import paddle, paddleocr
    print(f'PaddlePaddle: {paddle.__version__}')
    print('PaddleOCR: Available')
except ImportError as e:
    print(f'PaddleOCR: Not available - {e}')
\"
"

exit_code=$?

case $exit_code in
    0)
        echo "🎉 All packages install successfully!"
        echo "✅ Ready for Docker build"
        ;;
    1)
        echo "❌ Core dependencies failed (numpy, Pillow)"
        ;;
    2)
        echo "❌ Web framework failed (FastAPI, Uvicorn)"
        ;;
    3)
        echo "❌ Image processing failed (OpenCV, pytesseract)"
        ;;
    4)
        echo "❌ Document processing failed (reportlab, img2pdf)"
        ;;
    5)
        echo "❌ ONNX/rembg failed"
        ;;
    6)
        echo "❌ PaddlePaddle failed"
        ;;
    7)
        echo "❌ PaddleOCR failed"
        ;;
    *)
        echo "❌ Unknown error: $exit_code"
        ;;
esac

exit $exit_code
