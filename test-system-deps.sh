#!/bin/bash
# Test system dependencies for numpy and Pillow compilation
# This script identifies missing system libraries that cause pip install exit code 2

set -e

echo "🔍 Testing System Dependencies for Python Package Compilation"
echo "============================================================="

# Function to test dependency installation
test_deps() {
    local dockerfile=$1
    local description=$2
    
    echo ""
    echo "🧪 Testing: $description"
    echo "   Dockerfile: $dockerfile"
    
    if docker build -f "$dockerfile" -t test-deps . > /dev/null 2>&1; then
        echo "   ✅ SUCCESS: $description"
        docker rmi test-deps > /dev/null 2>&1
        return 0
    else
        echo "   ❌ FAILED: $description"
        return 1
    fi
}

# Function to test specific package installation
test_package_install() {
    local package=$1
    local description=$2
    
    echo ""
    echo "🧪 Testing package: $package ($description)"
    
    cat > test_package.dockerfile << EOF
FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential gcc g++ python3-dev pkg-config \\
    libjpeg-dev zlib1g-dev libpng-dev libtiff5-dev libfreetype6-dev \\
    libblas-dev liblapack-dev gfortran \\
    curl ca-certificates \\
 && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --verbose $package
RUN python -c "import ${package%>=*}; print('$package installed successfully')"
EOF

    if docker build -f test_package.dockerfile -t test-package . > /dev/null 2>&1; then
        echo "   ✅ $package installs successfully"
        docker rmi test-package > /dev/null 2>&1
        rm test_package.dockerfile
        return 0
    else
        echo "   ❌ $package installation failed"
        rm test_package.dockerfile
        return 1
    fi
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not available - cannot run dependency tests"
    echo "💡 Install Docker to run comprehensive dependency testing"
    exit 1
fi

echo "✅ Docker is available"

# Test 1: Basic dependency test
echo ""
echo "📋 Test 1: System Dependencies Test"
if test_deps "Dockerfile.test-deps" "System Dependencies for numpy and Pillow"; then
    echo "🎉 System dependencies are correctly configured!"
else
    echo "❌ System dependencies test failed"
    echo "💡 This indicates missing system libraries for compilation"
fi

# Test 2: Individual package tests
echo ""
echo "📋 Test 2: Individual Package Installation Tests"

packages=(
    "numpy>=1.20.0,<2.0.0:NumPy (numerical computing)"
    "Pillow>=9.0.0,<11.0.0:Pillow (image processing)"
    "opencv-python-headless>=4.8.0,<5.0.0:OpenCV (computer vision)"
)

all_packages_ok=true
for package_info in "${packages[@]}"; do
    IFS=':' read -r package description <<< "$package_info"
    if ! test_package_install "$package" "$description"; then
        all_packages_ok=false
    fi
done

# Test 3: Main Dockerfile test
echo ""
echo "📋 Test 3: Main Dockerfile Build Test"
if test_deps "Dockerfile" "Main Dockerfile with Fixed Dependencies"; then
    echo "🎉 Main Dockerfile builds successfully!"
    main_dockerfile_ok=true
else
    echo "❌ Main Dockerfile build failed"
    main_dockerfile_ok=false
fi

# Summary
echo ""
echo "=" * 60
echo "📊 Test Summary:"

if $all_packages_ok; then
    echo "✅ Individual packages: All packages install successfully"
else
    echo "❌ Individual packages: Some packages failed to install"
fi

if $main_dockerfile_ok; then
    echo "✅ Main Dockerfile: Builds successfully"
else
    echo "❌ Main Dockerfile: Build failed"
fi

echo ""
if $all_packages_ok && $main_dockerfile_ok; then
    echo "🎉 OVERALL RESULT: System dependencies are correctly configured!"
    echo "   Ready for production deployment"
    exit 0
else
    echo "❌ OVERALL RESULT: System dependency issues detected"
    echo ""
    echo "🔧 Troubleshooting suggestions:"
    echo "1. Ensure all required system libraries are installed"
    echo "2. Check for package availability in the base image"
    echo "3. Try the robust dependencies build (Dockerfile.robust-deps)"
    echo "4. Use the fallback build system (./build-with-fallbacks.sh)"
    exit 1
fi
