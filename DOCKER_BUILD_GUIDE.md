# Docker Build Guide - Solving Dependency Conflicts

## Problem Analysis

The Docker build failure (exit code 2) during pip install is caused by:

1. **Complex ML dependency conflicts** between PyTorch, PaddleOCR, Transformers, and ONNX Runtime
2. **Platform-specific package issues** with ONNX Runtime conditional installation
3. **Memory/resource constraints** during build process
4. **Missing system dependencies** for some ML packages

## Solution Strategy

### 🎯 **Default: Full Build with Complete ML Functionality**

The main `Dockerfile` is optimized for full functionality by default:

```bash
# Default build - Full ML functionality (Recommended)
docker build -t autocropper:latest .
```

**Features:**
- ✅ Complete ML functionality (PaddleOCR, background removal, transformers)
- ✅ Advanced image straightening with CNN-based orientation detection
- ✅ Background removal with rembg
- ✅ Enhanced PDF conversion with alpha channel handling
- ✅ Optimized staged installation with retry logic
- ✅ CPU-optimized PyTorch for production stability
- ✅ Extended timeouts and robust error handling

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
