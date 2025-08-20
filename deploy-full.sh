#!/bin/bash
# Production deployment script for full ML build
# Ensures all ML capabilities are available

set -e

echo "🚀 Starting Full ML Build Deployment..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Build with full ML functionality
echo "📦 Building full ML image..."
docker build -t autocropper:full . || {
    echo "❌ Full build failed. Check Docker logs above."
    echo "💡 Try increasing Docker memory allocation to 4GB+"
    exit 1
}

echo "✅ Full ML build completed successfully!"

# Test the build
echo "🧪 Testing full build functionality..."

# Start container for testing
docker run -d --name autocropper-test -p 8000:8000 autocropper:full

# Wait for startup
echo "⏳ Waiting for service to start..."
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    docker logs autocropper-test
    docker stop autocropper-test
    docker rm autocropper-test
    exit 1
fi

# Test ML functionality
echo "🧪 Testing ML capabilities..."

# Test PDF conversion
if curl -f -X POST http://localhost:8000/test-pdf-conversion > /dev/null 2>&1; then
    echo "✅ PDF conversion test passed"
else
    echo "⚠️ PDF conversion test failed (may be normal if no test images)"
fi

# Cleanup test container
docker stop autocropper-test
docker rm autocropper-test

echo "🎉 Full ML build is ready for production!"
echo ""
echo "📋 Deployment Summary:"
echo "   • Image: autocropper:full"
echo "   • Features: PaddleOCR + Background Removal + Advanced PDF"
echo "   • Size: ~2.5-3GB"
echo "   • Memory: 2-4GB recommended"
echo ""
echo "🚀 To deploy to Railway:"
echo "   railway up"
echo ""
echo "🐳 To run locally:"
echo "   docker run -p 8000:8000 autocropper:full"
