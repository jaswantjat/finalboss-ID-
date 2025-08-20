#!/usr/bin/env python3
"""
Verify Full ML Build Configuration
Checks that all ML dependencies and features are properly configured
"""

import sys
import importlib
from pathlib import Path

def check_dependency(name, package=None):
    """Check if a dependency is available"""
    try:
        if package:
            importlib.import_module(package)
        else:
            importlib.import_module(name)
        print(f"✅ {name}")
        return True
    except ImportError:
        print(f"❌ {name} - Not available")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - File not found: {filepath}")
        return False

def main():
    print("🔍 Verifying Full ML Build Configuration...\n")
    
    all_good = True
    
    # Check core dependencies
    print("📦 Core Dependencies:")
    all_good &= check_dependency("numpy")
    all_good &= check_dependency("PIL", "pillow")
    all_good &= check_dependency("cv2", "opencv-python-headless")
    all_good &= check_dependency("fastapi")
    all_good &= check_dependency("uvicorn")
    
    print("\n🧠 ML Dependencies:")
    all_good &= check_dependency("torch")
    all_good &= check_dependency("torchvision")
    all_good &= check_dependency("transformers")
    all_good &= check_dependency("onnxruntime")
    
    print("\n🎯 Specialized ML:")
    all_good &= check_dependency("paddleocr")
    all_good &= check_dependency("rembg")
    
    print("\n📄 Document Processing:")
    all_good &= check_dependency("pytesseract")
    all_good &= check_dependency("reportlab")
    all_good &= check_dependency("img2pdf")
    
    print("\n📁 Configuration Files:")
    all_good &= check_file_exists("Dockerfile", "Main Dockerfile (full build)")
    all_good &= check_file_exists("requirements.txt", "Main requirements (full ML)")
    all_good &= check_file_exists("railway.toml", "Railway configuration")
    all_good &= check_file_exists("deploy-full.sh", "Full deployment script")
    
    print("\n🔧 Optional Files:")
    check_file_exists("Dockerfile.minimal", "Minimal Dockerfile (fallback)")
    check_file_exists("requirements-minimal.txt", "Minimal requirements")
    check_file_exists("DOCKER_BUILD_GUIDE.md", "Build documentation")
    
    print("\n" + "="*50)
    
    if all_good:
        print("🎉 Full ML Build Configuration: VERIFIED")
        print("✅ All required dependencies and files are present")
        print("🚀 Ready for production deployment with complete ML functionality")
        return 0
    else:
        print("⚠️  Full ML Build Configuration: INCOMPLETE")
        print("❌ Some dependencies or files are missing")
        print("💡 Run 'pip install -r requirements.txt' to install missing dependencies")
        return 1

if __name__ == "__main__":
    sys.exit(main())
