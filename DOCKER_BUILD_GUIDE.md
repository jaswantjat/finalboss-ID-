# Docker Build Guide - Solving Dependency Conflicts

## Problem Analysis

The Docker build failure (exit code 2) during pip install is caused by:

1. **Complex ML dependency conflicts** between PyTorch, PaddleOCR, Transformers, and ONNX Runtime
2. **Platform-specific package issues** with ONNX Runtime conditional installation
3. **Memory/resource constraints** during build process
4. **Missing system dependencies** for some ML packages

## Solution Strategy

### 🎯 **Approach 1: Staged Installation (Recommended)**

Use the main `Dockerfile` with staged dependency installation:

```bash
# Build with staged installation
docker build -t autocropper:latest .
```

**Features:**
- ✅ Full ML functionality (PaddleOCR, background removal)
- ✅ Staged installation reduces conflicts
- ✅ CPU-optimized PyTorch for smaller size
- ✅ Comprehensive error handling

### 🚀 **Approach 2: Minimal Build (Fallback)**

If the full build fails, use the minimal version:

```bash
# Build minimal version (core functionality only)
docker build -f Dockerfile.minimal -t autocropper:minimal .
```

**Features:**
- ✅ Core image straightening and PDF conversion
- ✅ Fast build time
- ✅ Smaller image size
- ❌ No PaddleOCR (uses Tesseract OSD only)
- ❌ No background removal

### 🔧 **Approach 3: Local Development**

For local development without Docker:

```bash
# Install in stages locally
pip install -r requirements-base.txt
pip install -r requirements-ml.txt
```

## Build Options Comparison

| Feature | Full Build | Minimal Build |
|---------|------------|---------------|
| Image Straightening | ✅ PaddleOCR + Tesseract | ✅ Tesseract only |
| PDF Conversion | ✅ img2pdf + alpha handling | ✅ img2pdf + alpha handling |
| Background Removal | ✅ rembg | ❌ |
| Build Time | ~10-15 min | ~3-5 min |
| Image Size | ~2-3 GB | ~800 MB |
| Memory Usage | High | Low |

## Troubleshooting

### If Full Build Fails:

1. **Try minimal build first** to verify basic functionality
2. **Check Railway/platform memory limits** (may need to increase)
3. **Use local development** for testing

### Common Issues:

- **Out of memory**: Use minimal build or increase platform resources
- **Dependency conflicts**: Staged installation should resolve most issues
- **Platform compatibility**: CPU-only PyTorch improves compatibility

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
