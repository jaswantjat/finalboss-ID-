# Docker Build Guide - Comprehensive Solution for Build Failures

## Problem Analysis

Docker build failures can occur at different stages:

### **apt-get install failures (exit code 100)**:
1. **Package availability**: Some packages may not exist in the specific Debian version
2. **Repository issues**: Package lists may be outdated or repositories unavailable
3. **Package name changes**: Package names differ between Debian versions
4. **Missing dependencies**: Some packages require additional repositories

### **pip install failures (exit code 2)**:
1. **Complex ML dependency conflicts** between PyTorch, PaddleOCR, Transformers, and ONNX Runtime
2. **Platform-specific package issues** with ONNX Runtime conditional installation
3. **Memory/resource constraints** during build process
4. **Missing system dependencies** for some ML packages

## Solution Strategy

### 🎯 **Strategy 1: Automatic Build with Fallbacks (Recommended)**

Use the comprehensive build script that tries multiple approaches:

```bash
# Automatic build with fallback strategies
./build-with-fallbacks.sh
```

This script will try in order:
1. **Main Dockerfile** (full ML functionality)
2. **Dockerfile.robust** (enhanced package management)
3. **Dockerfile.fixed** (individual package error handling)
4. **Dockerfile.minimal** (core functionality only)

### 🚀 **Strategy 2: Manual Build Selection**

Choose a specific build approach:

```bash
# Full ML build (main)
docker build -t autocropper:full .

# Robust build (enhanced error handling)
docker build -f Dockerfile.robust -t autocropper:robust .

# Fixed build (individual package handling)
docker build -f Dockerfile.fixed -t autocropper:fixed .

# Minimal build (core functionality)
docker build -f Dockerfile.minimal -t autocropper:minimal .
```

### 🚀 **Fallback: Minimal Build (Emergency Only)**

Only use if the full build fails due to resource constraints:

```bash
# Minimal build (fallback only)
docker build -f Dockerfile.minimal -t autocropper:minimal .
```

**Features:**
- ✅ Core image straightening and PDF conversion
- ✅ Fast build time (~3-5 min)
- ✅ Smaller image size (~800 MB)
- ❌ No PaddleOCR (Tesseract OSD only)
- ❌ No background removal
- ❌ Limited ML capabilities

### 🔧 **Approach 3: Local Development**

For local development without Docker:

```bash
# Install in stages locally
pip install -r requirements-base.txt
pip install -r requirements-ml.txt
```

## Build Options Comparison

| Feature | Full Build (Default) | Minimal Build (Fallback) |
|---------|---------------------|---------------------------|
| Image Straightening | ✅ PaddleOCR CNN + Tesseract OSD | ⚠️ Tesseract OSD only |
| PDF Conversion | ✅ img2pdf + alpha handling | ✅ img2pdf + alpha handling |
| Background Removal | ✅ rembg with ONNX models | ❌ Not available |
| Auto-rotation | ✅ EXIF + CNN + Hough lines | ⚠️ EXIF + basic skew only |
| Build Time | ~15-20 min | ~3-5 min |
| Image Size | ~2.5-3 GB | ~800 MB |
| Memory Usage | 2-4 GB | 512 MB - 1 GB |
| Production Ready | ✅ Full feature set | ⚠️ Limited capabilities |

## Comprehensive Troubleshooting

### **apt-get install failures (exit code 100)**

**Symptoms**: Build fails during system package installation
**Solutions**:
1. **Use Dockerfile.fixed**: Handles packages individually with error handling
2. **Check base image**: Ensure using `python:3.11-slim-bookworm`
3. **Update package lists**: Some builds include `apt-get update` before each group
4. **Package alternatives**: Script tries multiple package names for same functionality

```bash
# Debug specific package availability
docker run --rm python:3.11-slim-bookworm bash -c "apt-get update && apt-cache search tesseract"
```

### **pip install failures (exit code 2)**

**Symptoms**: Build fails during Python package installation with exit code 2
**Root Cause**: Missing system libraries required for compiling Python packages

**Common Causes**:
- **numpy**: Requires math libraries (`libblas-dev`, `liblapack-dev`, `gfortran`)
- **Pillow**: Requires image format libraries (`libjpeg-dev`, `zlib1g-dev`, `libpng-dev`, `libtiff5-dev`, `libfreetype6-dev`)
- **OpenCV**: Requires additional system libraries
- **python:3.11-slim**: Missing development headers and libraries

**Solutions**:
1. **System Dependencies**: Install comprehensive build libraries (implemented in main Dockerfile)
2. **Staged Installation**: Install packages in logical groups to isolate failures
3. **Robust Dependencies**: Use Dockerfile.robust-deps with fallback package names
4. **Memory issues**: Increase Docker memory allocation to 4GB+
5. **Testing**: Use test-system-deps.sh to verify dependency configuration

### **Build Strategy Selection**

**If main build fails**:
1. ✅ Try `./build-with-fallbacks.sh` (automatic fallback)
2. ✅ Try `Dockerfile.robust` (enhanced package management)
3. ✅ Try `Dockerfile.fixed` (individual error handling)
4. ✅ Try `Dockerfile.minimal` (core functionality only)

### **Platform-Specific Issues**

**Railway/Cloud Platforms**:
- Increase memory allocation in platform settings
- Use CPU-only builds (already configured)
- Consider using minimal build for resource constraints

**Local Development**:
- Increase Docker Desktop memory allocation
- Ensure stable internet connection for package downloads
- Try building during off-peak hours

## Railway Deployment

For Railway deployment, the platform will automatically:
1. Try the main `Dockerfile` first
2. Fall back to `Dockerfile.minimal` if needed
3. Use appropriate memory allocation

## Testing

After successful build, test the endpoints:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test PDF conversion
curl -X POST http://localhost:8000/test-pdf-conversion

# Test image straightening
curl -X POST http://localhost:8000/straighten \
  -F "file=@test_image.jpg" \
  -o straightened.png
```

## Recommendations

1. **Start with minimal build** to verify deployment works
2. **Upgrade to full build** once basic functionality is confirmed
3. **Monitor resource usage** during deployment
4. **Use staged installation** for production deployments
