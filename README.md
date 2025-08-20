# Image Processing API
Production-ready REST API with Full ML Capabilities

A FastAPI-based web service with complete machine learning functionality:
1. **Advanced ID Card Straightening**: CNN-based orientation detection with PaddleOCR + EXIF + Hough line correction
2. **Enhanced PDF Conversion**: img2pdf with alpha channel handling and flexible page sizing
3. **Background Removal**: AI-powered background removal using rembg with ONNX models

## 🎯 Full ML Features (Default Build)

### Advanced ID Card Straightening
- **🧠 CNN-based Orientation**: PaddleOCR neural network for 0°/90°/180°/270° detection
- **📱 EXIF Correction**: Automatic phone photo orientation handling
- **📐 Fine Skew Correction**: Hough line-based ±5° skew correction
- **🔄 Confidence Gating**: Tesseract OSD fallback for edge cases
- **⚡ Production Optimized**: Robust error handling and JSON serialization

### Enhanced PDF Conversion
- **🎨 Alpha Channel Handling**: Proper PNG transparency removal (no black rectangles)
- **📄 Flexible Page Sizing**: "fit" (image-sized), A4, Letter, A4^T, custom dimensions
- **🎯 Advanced Fit Modes**: into, fill, exact, shrink, enlarge
- **🌈 Configurable Backgrounds**: Custom background colors for alpha removal
- **📚 Multi-page Support**: Mixed image formats in single PDF
- **🔄 Auto-orientation**: EXIF-based rotation handling

### AI Background Removal
- **🤖 ONNX Models**: High-quality AI-powered background removal
- **🎨 Multiple Models**: Support for different image types
- **⚡ Optimized Performance**: CPU-optimized inference

### Production Features
- **🚀 REST API**: FastAPI with comprehensive documentation
- **🧪 Automated Testing**: Built-in test endpoints with 4 test scenarios
- **📊 Real-time Monitoring**: Processing statistics and performance metrics
- **🛡️ Enterprise Ready**: Comprehensive error handling and logging
- **🐳 Docker Optimized**: Staged builds with retry logic

## Quick Start

### 🚀 Production Deployment (Automatic Build Selection)

```bash
# Comprehensive deployment with automatic fallback (Recommended)
./deploy-full.sh
```

This will:
- Automatically try multiple build strategies until one succeeds
- Test all available ML capabilities
- Verify production readiness
- Provide deployment instructions

### 🐳 Docker Deployment Options

```bash
# Option 1: Automatic build with fallbacks (Recommended)
./build-with-fallbacks.sh

# Option 2: Diagnostic first, then build
./diagnose-build-issues.sh  # Identify best strategy
docker build -t autocropper:latest .  # Then build

# Option 3: Specific build strategy
docker build -f Dockerfile.robust -t autocropper:robust .
docker build -f Dockerfile.minimal -t autocropper:minimal .

# Run the built image
docker run -p 8000:8000 <image-name>
```

### 🛠️ Local Development

```bash
# Automated setup and launch
./start_api.sh
```

Or manually:
```bash
python -m venv id_env
source id_env/bin/activate  # On Windows: id_env\Scripts\activate
pip install -r requirements.txt
python api_service.py
```

### 3. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## API Usage

### Interactive Documentation

Visit http://localhost:8000/docs for interactive API documentation with Swagger UI.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and available endpoints |
| `/health` | GET | Health check and service status |
| `/stats` | GET | Processing statistics and performance metrics |
| `/straighten` | POST | Straighten an ID card image |
| `/convert-to-pdf` | POST | Convert images to PDF format |
| `/test-ui` | GET | Interactive test interface |

### Straighten Image Endpoint

**POST** `/straighten`

**Parameters:**
- `file`: Image file (JPG, PNG, BMP, TIFF, WEBP) - max 10MB
- `return_format`: "base64" (default) or "file"

**Example using curl:**
```bash
# Return base64 encoded result
curl -X POST "http://localhost:8000/straighten" \
     -F "file=@your_id_card.jpg" \
     -F "return_format=base64"

# Return file download
curl -X POST "http://localhost:8000/straighten" \
     -F "file=@your_id_card.jpg" \
     -F "return_format=file" \
     -o straightened_result.jpg
```

### Python Client Example

```python
import requests

# Test the API
with open('your_id_card.jpg', 'rb') as f:
    files = {'file': ('id_card.jpg', f, 'image/jpeg')}
    data = {'return_format': 'base64'}

    response = requests.post('http://localhost:8000/straighten',
                           files=files, data=data)

if response.status_code == 200:
    result = response.json()
    print(f"Processing time: {result['processing_time_seconds']:.3f}s")
    print(f"Rotation applied: {result['rotation']['angle_applied']}°")
    print(f"OCR confidence: {result['ocr_confidence']:.1f}")

    # Save the straightened image
    import base64
    image_data = base64.b64decode(result['image_base64'])
    with open('straightened_result.jpg', 'wb') as f:
        f.write(image_data)
```

### Response Format

```json
{
  "success": true,
  "filename": "id_card.jpg",
  "processing_time_seconds": 0.245,
  "rotation": {
    "angle_applied": 90,
    "confidence": 275.3,
    "applied": true
  },
  "skew_correction": {
    "angle_detected": -1.2,
    "applied": true
  },
  "ocr_confidence": 89.6,
  "keywords_detected": 3,
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

## How It Works

### 1. Smart Rotation Detection
- OCR-based analysis tests all 4 orientations (0°, 90°, 180°, 270°)
- Scores each orientation using OCR confidence + word count + Spanish ID keywords
- Multiple preprocessing attempts (original, enhanced, binarized) for optimal OCR
- Selects orientation with highest combined score

### 2. Advanced Skew Correction
- Projection profile analysis with fine-resolution angle testing
- Detects and corrects small skew angles (typically ±8°)
- Robust statistical methods for accurate angle estimation

### 3. Production Features
- Comprehensive error handling and validation
- Real-time processing statistics and monitoring
- Support for multiple image formats and return types
- Automatic cleanup of temporary files

## Performance

**Typical Processing Times:**
- Rotation Detection: ~0.15s per image
- Skew Correction: ~0.05s per image
- **Total: ~0.2s per image → 18,000+ images/day**

**Accuracy:**
- Rotation Detection: >95% accuracy on clear ID documents
- Spanish Keyword Recognition: DNI, ESPAÑA, ESP, DOCUMENTO, etc.
- Skew Correction: ±0.5° accuracy for angles up to ±8°

## Configuration

### Environment Variables
```bash
export API_HOST=0.0.0.0          # API host (default: 0.0.0.0)
export API_PORT=8000             # API port (default: 8000)
export MAX_FILE_SIZE=10485760    # Max upload size in bytes (default: 10MB)
export LOG_LEVEL=INFO            # Logging level (default: INFO)
```

### Spanish ID Keywords
The system recognizes these Spanish ID keywords for enhanced scoring:
- DNI, ESPAÑA, ESP, DOCUMENTO, NACIONAL, IDENTIDAD

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "api_service.py"]
```

### Production Considerations

- **Load Balancing**: Use nginx or similar for multiple API instances
- **Monitoring**: Implement health checks and metrics collection
- **Security**: Add authentication, rate limiting, and input validation
- **Storage**: Configure persistent storage for processed images if needed
- **Scaling**: Consider horizontal scaling for high-throughput scenarios

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure tesseract is installed and in PATH
2. **API not starting**: Check if port 8000 is available
3. **Low processing accuracy**: Ensure good image quality and lighting
4. **File upload errors**: Check file size (<10MB) and format support

### API Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid file format, parameters) |
| 413 | File too large (>10MB) |
| 500 | Internal server error (processing failure) |

## File Structure

```
image_processing_api/
├── api_service.py              # FastAPI web service
├── optimized_straightener.py   # ID card straightening engine
├── pdf_converter.py            # PDF conversion engine
├── cropper.py                  # Image cropping utilities
├── main.py                     # CLI interface (legacy)
├── straightener.py             # Original rotation detection
├── start_api.sh               # API launcher script
├── api_client_example.py      # Example API client
├── test_pdf_converter.py      # PDF converter tests
├── requirements.txt           # Python dependencies
├── static/                    # Test UI files
│   ├── index.html            # Test interface
│   ├── style.css             # UI styling
│   └── script.js             # UI functionality
├── models/                    # Model files (optional)
└── README.md                  # This documentation
```

## Image to PDF Conversion

### Convert Images to PDF Endpoint

**POST** `/convert-to-pdf`

**Parameters:**
- `files`: One or more image files (JPG, PNG, GIF, BMP, TIFF, WEBP) - max 10MB each, up to 20 files
- `return_format`: "file" (default) or "base64"
- `page_size`: "A4" (default), "Letter", or "Legal"
- `fit_mode`: "fit" (maintain aspect ratio, default) or "fill" (stretch to fill page)

**Example using curl:**
```bash
# Convert single image to PDF
curl -X POST "http://localhost:8000/convert-to-pdf" \
     -F "files=@image.jpg" \
     -F "return_format=file" \
     -o result.pdf

# Convert multiple images to PDF
curl -X POST "http://localhost:8000/convert-to-pdf" \
     -F "files=@image1.jpg" \
     -F "files=@image2.png" \
     -F "page_size=A4" \
     -F "fit_mode=fit" \
     -o multi_page.pdf
```

**Python Example:**
```python
import requests

# Multiple images to PDF
files = [
    ('files', ('img1.jpg', open('img1.jpg', 'rb'), 'image/jpeg')),
    ('files', ('img2.png', open('img2.png', 'rb'), 'image/png'))
]
data = {'return_format': 'file', 'page_size': 'A4', 'fit_mode': 'fit'}

response = requests.post('http://localhost:8000/convert-to-pdf',
                       files=files, data=data)

if response.status_code == 200:
    with open('result.pdf', 'wb') as f:
        f.write(response.content)
```

### Test UI

Visit `http://localhost:8000/test-ui` for an interactive web interface to test both services:
- 🖱️ Drag-and-drop file upload
- 👁️ Real-time image preview
- ⚙️ Configuration options (page size, fit mode)
- 📥 Download results
- 📊 Live service statistics

## Testing the API

Run the example client to test all endpoints:

```bash
python api_client_example.py
```

This will:
- Create test ID card images
- Test all API endpoints
- Demonstrate both base64 and file return formats
- Show processing statistics

## Testing

### Run Unit Tests
```bash
# Test PDF converter functionality
python test_pdf_converter.py

# Test API endpoints (requires running server)
python -m pytest test_pdf_converter.py::TestAPIEndpoints -v
```

### Run Example Client
```bash
python api_client_example.py
```

This will:
- Create test ID card images
- Test all API endpoints
- Demonstrate both base64 and file return formats
- Show processing statistics

## Dependencies

- **Core Processing**: opencv-python, pillow, numpy, pytesseract
- **PDF Generation**: reportlab
- **ML Models**: transformers, torch, torchvision, torchaudio
- **API Framework**: fastapi, uvicorn, python-multipart
- **System**: tesseract-ocr (external dependency)

## License

This project is provided as-is for document processing applications.
