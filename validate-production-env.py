#!/usr/bin/env python3
"""
Production Environment Validation Script
Validates all the fixes implemented for Railway deployment issues
"""

import sys
import subprocess
import os
import importlib

def check_tesseract():
    """Check Tesseract installation and language packs"""
    print("🔍 Checking Tesseract OCR...")
    
    try:
        # Check Tesseract version
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        version = result.stderr.split('\n')[0] if result.stderr else "Unknown"
        print(f"   ✅ Tesseract version: {version}")
        
        # Check available languages
        lang_result = subprocess.run(['tesseract', '--list-langs'], 
                                   capture_output=True, text=True, timeout=5)
        if lang_result.returncode == 0:
            langs = lang_result.stdout.strip().split('\n')[1:]  # Skip header
            print(f"   ✅ Available languages: {', '.join(langs[:10])}")
            
            # Check critical language packs
            has_osd = 'osd' in langs
            has_spanish = 'spa' in langs
            has_english = 'eng' in langs
            
            print(f"   {'✅' if has_osd else '❌'} OSD (Orientation and Script Detection): {'Available' if has_osd else 'Missing'}")
            print(f"   {'✅' if has_spanish else '⚠️'} Spanish (spa): {'Available' if has_spanish else 'Missing'}")
            print(f"   {'✅' if has_english else '❌'} English (eng): {'Available' if has_english else 'Missing'}")
            
            return has_osd and has_english
        else:
            print("   ❌ Could not list Tesseract languages")
            return False
            
    except Exception as e:
        print(f"   ❌ Tesseract check failed: {e}")
        return False

def check_paddleocr():
    """Check PaddleOCR and PaddlePaddle installation"""
    print("\n🧠 Checking PaddleOCR...")
    
    # Check PaddlePaddle
    try:
        import paddle
        print(f"   ✅ PaddlePaddle version: {paddle.__version__}")
        paddle_ok = True
    except ImportError:
        print("   ❌ PaddlePaddle not installed")
        paddle_ok = False
    except Exception as e:
        print(f"   ❌ PaddlePaddle error: {e}")
        paddle_ok = False
    
    # Check PaddleOCR
    try:
        import paddleocr
        print(f"   ✅ PaddleOCR available")
        
        # Try to initialize orientation classifier
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            print("   ✅ PaddleOCR orientation classifier initialized")
            paddleocr_ok = True
        except Exception as e:
            print(f"   ⚠️ PaddleOCR initialization warning: {e}")
            paddleocr_ok = False
            
    except ImportError:
        print("   ❌ PaddleOCR not installed")
        paddleocr_ok = False
    except Exception as e:
        print(f"   ❌ PaddleOCR error: {e}")
        paddleocr_ok = False
    
    return paddle_ok and paddleocr_ok

def check_opencv():
    """Check OpenCV installation"""
    print("\n📷 Checking OpenCV...")
    
    try:
        import cv2
        print(f"   ✅ OpenCV version: {cv2.__version__}")
        
        # Check if it's headless
        is_headless = not hasattr(cv2, 'imshow')
        print(f"   {'✅' if is_headless else '⚠️'} Headless version: {'Yes' if is_headless else 'No (GUI dependencies present)'}")
        
        return True
    except ImportError:
        print("   ❌ OpenCV not installed")
        return False
    except Exception as e:
        print(f"   ❌ OpenCV error: {e}")
        return False

def check_other_dependencies():
    """Check other critical dependencies"""
    print("\n📦 Checking other dependencies...")
    
    deps = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'rembg': 'Background Removal',
        'onnxruntime': 'ONNX Runtime',
        'pytesseract': 'PyTesseract',
        'reportlab': 'ReportLab',
        'img2pdf': 'img2pdf'
    }
    
    all_ok = True
    for module, name in deps.items():
        try:
            mod = importlib.import_module(module)
            version = getattr(mod, '__version__', 'Unknown')
            print(f"   ✅ {name}: {version}")
        except ImportError:
            print(f"   ❌ {name}: Not installed")
            all_ok = False
        except Exception as e:
            print(f"   ⚠️ {name}: {e}")
    
    return all_ok

def check_environment_variables():
    """Check critical environment variables"""
    print("\n🌍 Checking environment variables...")
    
    env_vars = {
        'TESSDATA_PREFIX': '/usr/share/tesseract-ocr/4.00/tessdata',
        'OMP_THREAD_LIMIT': '1',
        'UVICORN_WORKERS': '1',
        'PYTHONUNBUFFERED': '1'
    }
    
    for var, expected in env_vars.items():
        value = os.getenv(var)
        if value:
            status = '✅' if value == expected else '⚠️'
            print(f"   {status} {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set (expected: {expected})")

def check_rembg_model():
    """Check if rembg model is baked in"""
    print("\n🎨 Checking rembg model...")
    
    model_path = '/root/.u2net/u2net.onnx'
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"   ✅ u2net.onnx model baked in: {size_mb:.1f} MB")
        return True
    else:
        print("   ⚠️ u2net.onnx model not baked in (will download on first use)")
        return False

def main():
    """Run all validation checks"""
    print("🔍 Production Environment Validation")
    print("=" * 50)
    
    checks = [
        ("Tesseract OCR", check_tesseract),
        ("PaddleOCR", check_paddleocr),
        ("OpenCV", check_opencv),
        ("Dependencies", check_other_dependencies),
        ("Environment", check_environment_variables),
        ("rembg Model", check_rembg_model)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ {name} check failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    
    all_critical_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {name}")
        
        # Critical checks that must pass
        if name in ["Tesseract OCR", "OpenCV", "Dependencies"] and not passed:
            all_critical_passed = False
    
    print("\n" + "=" * 50)
    if all_critical_passed:
        print("🎉 Production environment validation: PASSED")
        print("   Ready for Railway deployment!")
        return 0
    else:
        print("❌ Production environment validation: FAILED")
        print("   Critical issues found - fix before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
