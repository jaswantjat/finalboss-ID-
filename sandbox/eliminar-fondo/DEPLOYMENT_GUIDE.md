# Background Removal API - Production Deployment Guide

## ✅ Production-Ready API

This is a clean, production-ready FastAPI service for AI-powered background removal. All development artifacts have been removed and the application is optimized for API-only usage.

### 🏗️ Architecture

- **FastAPI**: Modern, fast web framework with automatic API documentation
- **AI Background Removal**: Uses `rembg` library with ONNX models
- **Docker**: Containerized for consistent deployment across platforms
- **Health Checks**: Built-in monitoring endpoints
- **Security**: Runs as non-root user in container

## 🚀 API Endpoints

### Core Endpoints

- **POST /remove_bg** - Remove background from image
- **GET /** - API information and usage examples
- **GET /health** - Health check for monitoring
- **GET /docs** - Interactive API documentation (Swagger UI)
- **GET /redoc** - Alternative API documentation

### Usage Examples

**cURL:**
```bash
curl -X POST "http://localhost:7860/remove_bg" \
     -F "file=@your_image.jpg" \
     --output result.png
```

**Python:**
```python
import requests

url = "http://localhost:7860/remove_bg"
files = {'file': ('image.jpg', open('image.jpg', 'rb'), 'image/jpeg')}
response = requests.post(url, files=files)

if response.status_code == 200:
    with open('result.png', 'wb') as f:
        f.write(response.content)
```

## 🚀 Deployment Options

### Option 1: Railway (Recommended)

1. **Create GitHub Repository**:
   ```bash
   cd sandbox/eliminar-fondo/Eliminar-Fondo-Imagen
   git init
   git add .
   git commit -m "Initial commit: Production API"
   git remote add origin https://github.com/yourusername/background-removal-api.git
   git push -u origin main
   ```

2. **Deploy to Railway**:
   - Visit https://railway.app
   - Connect your GitHub account
   - Create new project from GitHub repository
   - Railway auto-detects Dockerfile and deploys
   - Get your production URL: `https://your-app.up.railway.app`

3. **Environment Variables** (automatically configured):
   - `PORT` - Set by Railway
   - No additional configuration needed

### Option 2: Other Platforms

- **Render**: `render.com` - Similar to Railway, auto-detects Docker
- **Fly.io**: `fly.io` - Global edge deployment
- **Google Cloud Run**: Serverless container platform
- **AWS App Runner**: Container-based deployment on AWS
- **DigitalOcean App Platform**: Simple container deployment

### Option 3: Local Docker Testing

```bash
cd sandbox/eliminar-fondo/Eliminar-Fondo-Imagen

# Build the image
docker build -t background-removal-api .

# Run locally
docker run -p 7860:7860 background-removal-api

# Test the API
curl -X POST "http://localhost:7860/remove_bg" \
     -F "file=@test_image.jpg" \
     --output result.png
```

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:7860/health
```

### API Information
```bash
curl http://localhost:7860/
```

### Interactive Documentation
Visit `http://localhost:7860/docs` in your browser for Swagger UI

### Background Removal Test
```bash
# Test with a sample image
curl -X POST "http://localhost:7860/remove_bg" \
     -F "file=@your_image.jpg" \
     -H "accept: image/png" \
     --output result.png
```

## 📁 File Structure

```
sandbox/eliminar-fondo/
├── Eliminar-Fondo-Imagen/          # Cloned and fixed Hugging Face Space
│   ├── app.py                      # Main Gradio application
│   ├── requirements.txt            # Fixed dependencies
│   ├── Dockerfile                  # Container configuration
│   ├── .dockerignore              # Docker ignore rules
│   └── .venv/                     # Virtual environment (local only)
├── test_client.py                  # Test client for API
└── DEPLOYMENT_GUIDE.md            # This guide
```

## 🔧 Key Fixes Applied

1. **Dependency Resolution**:
   - Pinned numpy<2 to avoid compatibility issues
   - Added platform-specific onnxruntime packages
   - Updated to opencv-python-headless for containerization

2. **App Configuration**:
   - Modified app.py to bind to 0.0.0.0 (required for containers)
   - Added PORT environment variable support
   - Removed inline pip installs for cleaner deployment

3. **Docker Optimization**:
   - Multi-stage friendly Dockerfile
   - Proper .dockerignore to reduce image size
   - Environment variable configuration

## 🌐 API Endpoints

Once deployed, the app exposes:
- **Web UI**: `https://your-app.railway.app/`
- **API**: `https://your-app.railway.app/api/predict`

## 🎯 Usage Examples

### Web Interface
Visit the deployed URL in your browser and use the Gradio interface.

### API Usage
```python
import requests

url = "https://your-app.railway.app/api/predict"
files = {'data': ('image.jpg', open('image.jpg', 'rb'), 'image/jpeg')}
response = requests.post(url, files=files)

if response.status_code == 200:
    with open('result.png', 'wb') as f:
        f.write(response.content)
```

## 🛠️ Troubleshooting

1. **Local app won't start**: Check that all dependencies are installed in the virtual environment
2. **Docker build fails**: Ensure Docker is installed and running
3. **Railway deployment fails**: Check logs in Railway dashboard
4. **API returns errors**: Verify image format and size (should be reasonable size, common formats)

## 📞 Support

The app is now ready for deployment! The test client will help verify everything works correctly both locally and after deployment.
