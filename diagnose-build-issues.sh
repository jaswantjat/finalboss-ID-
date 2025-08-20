#!/bin/bash
# Docker Build Diagnostic Script
# Helps identify specific package availability and build issues

set -e

echo "🔍 Docker Build Diagnostic Tool"
echo "==============================="

# Function to check Docker availability
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    echo "✅ Docker is available: $(docker --version)"
}

# Function to check base image
check_base_image() {
    echo ""
    echo "📦 Checking base image availability..."
    
    if docker pull python:3.11-slim-bookworm > /dev/null 2>&1; then
        echo "✅ Base image python:3.11-slim-bookworm is available"
    else
        echo "❌ Base image python:3.11-slim-bookworm is not available"
        echo "   Trying alternative: python:3.11-slim"
        if docker pull python:3.11-slim > /dev/null 2>&1; then
            echo "✅ Alternative base image python:3.11-slim is available"
        else
            echo "❌ No suitable base image found"
            return 1
        fi
    fi
}

# Function to check package availability
check_packages() {
    echo ""
    echo "📋 Checking system package availability..."
    
    # Test essential packages
    local packages=(
        "build-essential"
        "gcc"
        "g++"
        "curl"
        "wget"
        "tesseract-ocr"
        "tesseract-ocr-eng"
        "tesseract-ocr-spa"
        "tesseract-ocr-osd"
        "libglib2.0-0"
        "libsm6"
        "libxext6"
        "libxrender-dev"
        "libgomp1"
        "libgfortran5"
        "libgl1-mesa-glx"
        "libgl1-mesa-dev"
        "libgl1"
    )
    
    echo "Testing package availability in python:3.11-slim-bookworm..."
    
    for package in "${packages[@]}"; do
        if docker run --rm python:3.11-slim-bookworm bash -c "apt-get update > /dev/null 2>&1 && apt-cache show $package > /dev/null 2>&1"; then
            echo "✅ $package"
        else
            echo "❌ $package - Not available"
        fi
    done
}

# Function to test minimal build
test_minimal_build() {
    echo ""
    echo "🧪 Testing minimal system package installation..."
    
    cat > test_minimal.dockerfile << 'EOF'
FROM python:3.11-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        tesseract-ocr \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
RUN echo "Minimal build test successful"
EOF

    if docker build -f test_minimal.dockerfile -t test-minimal . > /dev/null 2>&1; then
        echo "✅ Minimal system packages install successfully"
        docker rmi test-minimal > /dev/null 2>&1
    else
        echo "❌ Minimal system packages installation failed"
        echo "   This indicates a fundamental issue with the base image or repositories"
    fi
    
    rm -f test_minimal.dockerfile
}

# Function to check Python package installation
test_python_packages() {
    echo ""
    echo "🐍 Testing Python package installation..."
    
    cat > test_python.dockerfile << 'EOF'
FROM python:3.11-slim-bookworm
RUN pip install --no-cache-dir numpy pillow opencv-python-headless
RUN echo "Python packages test successful"
EOF

    if docker build -f test_python.dockerfile -t test-python . > /dev/null 2>&1; then
        echo "✅ Core Python packages install successfully"
        docker rmi test-python > /dev/null 2>&1
    else
        echo "❌ Core Python packages installation failed"
        echo "   This may indicate network issues or pip problems"
    fi
    
    rm -f test_python.dockerfile
}

# Function to provide recommendations
provide_recommendations() {
    echo ""
    echo "💡 Recommendations based on diagnostic results:"
    echo ""
    
    if docker images | grep -q "test-minimal"; then
        docker rmi test-minimal > /dev/null 2>&1
    fi
    
    if docker images | grep -q "test-python"; then
        docker rmi test-python > /dev/null 2>&1
    fi
    
    echo "1. 🎯 **Build Strategy Selection**:"
    echo "   - If minimal packages work: Try Dockerfile.minimal first"
    echo "   - If packages fail individually: Use Dockerfile.fixed"
    echo "   - For maximum compatibility: Use build-with-fallbacks.sh"
    echo ""
    echo "2. 🔧 **Platform Optimization**:"
    echo "   - Increase Docker memory allocation to 4GB+"
    echo "   - Ensure stable internet connection"
    echo "   - Consider building during off-peak hours"
    echo ""
    echo "3. 🚀 **Quick Start Commands**:"
    echo "   ./build-with-fallbacks.sh    # Automatic fallback strategy"
    echo "   ./deploy-full.sh             # Full deployment with testing"
    echo ""
    echo "4. 📋 **Available Dockerfiles**:"
    echo "   - Dockerfile (main, full ML)"
    echo "   - Dockerfile.robust (enhanced error handling)"
    echo "   - Dockerfile.fixed (individual package handling)"
    echo "   - Dockerfile.minimal (core functionality)"
}

# Main execution
main() {
    check_docker
    check_base_image
    check_packages
    test_minimal_build
    test_python_packages
    provide_recommendations
    
    echo ""
    echo "🎉 Diagnostic complete! Use the recommendations above to choose the best build strategy."
}

# Run main function
main "$@"
