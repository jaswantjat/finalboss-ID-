#!/bin/bash
# Comprehensive Docker build script with multiple fallback strategies
# Tries different Dockerfiles until one succeeds

set -e

echo "🔧 Comprehensive Docker Build with Fallback Strategies"
echo "======================================================"

# Function to test if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    echo "✅ Docker is available"
}

# Function to build with a specific Dockerfile
try_build() {
    local dockerfile=$1
    local tag=$2
    local description=$3
    
    echo ""
    echo "🚀 Attempting: $description"
    echo "   Dockerfile: $dockerfile"
    echo "   Tag: $tag"
    echo "   $(date)"
    
    if docker build -f "$dockerfile" -t "$tag" .; then
        echo "✅ SUCCESS: $description"
        return 0
    else
        echo "❌ FAILED: $description"
        return 1
    fi
}

# Function to test a built image
test_image() {
    local tag=$1
    echo "🧪 Testing image: $tag"
    
    # Start container
    if docker run -d --name test-container -p 8000:8000 "$tag"; then
        echo "✅ Container started successfully"
        
        # Wait for startup
        sleep 10
        
        # Test health endpoint
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Health check passed"
            docker stop test-container
            docker rm test-container
            return 0
        else
            echo "⚠️ Health check failed"
            docker logs test-container
            docker stop test-container
            docker rm test-container
            return 1
        fi
    else
        echo "❌ Container failed to start"
        return 1
    fi
}

# Main build process
main() {
    echo "🔍 Starting comprehensive build process..."
    
    check_docker
    
    # Strategy 1: Try the main Dockerfile (staged ML build)
    if try_build "Dockerfile" "autocropper:full" "Staged ML Build (Main Dockerfile)"; then
        echo "🎉 Staged build succeeded!"
        if test_image "autocropper:full"; then
            echo "🎯 FINAL RESULT: Staged ML build is working perfectly!"
            echo "   Image: autocropper:full"
            echo "   Features: Complete ML stack with PaddleOCR, rembg (staged installation)"
            exit 0
        fi
    fi

    echo "⚠️ Staged build failed, trying core functionality..."

    # Strategy 1.5: Try core functionality build
    if try_build "Dockerfile.core" "autocropper:core" "Core Functionality Build"; then
        echo "🎉 Core build succeeded!"
        if test_image "autocropper:core"; then
            echo "🎯 FINAL RESULT: Core build is working!"
            echo "   Image: autocropper:core"
            echo "   Features: Essential functionality (FastAPI, OpenCV, PDF, Tesseract)"
            echo "   Note: No PaddleOCR or background removal"
            exit 0
        fi
    fi
    
    echo "⚠️ Main build failed, trying robust approach..."
    
    # Strategy 2: Try the robust Dockerfile
    if try_build "Dockerfile.robust" "autocropper:robust" "Robust Build with Comprehensive Packages"; then
        echo "🎉 Robust build succeeded!"
        if test_image "autocropper:robust"; then
            echo "🎯 FINAL RESULT: Robust build is working!"
            echo "   Image: autocropper:robust"
            echo "   Features: Full ML stack with enhanced package management"
            exit 0
        fi
    fi
    
    echo "⚠️ Robust build failed, trying minimal approach..."
    
    # Strategy 3: Try the minimal Dockerfile
    if try_build "Dockerfile.minimal" "autocropper:minimal" "Minimal Build (Core Functionality)"; then
        echo "🎉 Minimal build succeeded!"
        if test_image "autocropper:minimal"; then
            echo "🎯 FINAL RESULT: Minimal build is working!"
            echo "   Image: autocropper:minimal"
            echo "   Features: Core functionality (image processing + PDF)"
            echo "   Note: Limited ML capabilities"
            exit 0
        fi
    fi
    
    echo "❌ All build strategies failed!"
    echo ""
    echo "🔧 Troubleshooting suggestions:"
    echo "1. Check Docker memory allocation (increase to 4GB+)"
    echo "2. Check internet connectivity for package downloads"
    echo "3. Try building on a different platform/architecture"
    echo "4. Check Docker logs for specific error details"
    echo ""
    echo "📋 Available Dockerfiles:"
    echo "   - Dockerfile (main, full ML)"
    echo "   - Dockerfile.robust (enhanced package management)"
    echo "   - Dockerfile.minimal (core functionality only)"
    
    exit 1
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up test containers..."
    docker stop test-container 2>/dev/null || true
    docker rm test-container 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"
