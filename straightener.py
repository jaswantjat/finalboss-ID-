# straightener.py
from PIL import Image
import cv2, pytesseract, numpy as np, os

# Simple rotation detection fallback (without external model)
def _simple_rotation_check(img_path):
    """Simple heuristic to check if image might be rotated"""
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False

    # Check aspect ratio - most ID cards are wider than tall
    h, w = img.shape
    if h > w:  # Taller than wide suggests rotation
        return True

    # Simple edge detection to check orientation
    edges = cv2.Canny(img, 50, 150)
    horizontal_edges = np.sum(edges, axis=1)
    vertical_edges = np.sum(edges, axis=0)

    # If vertical edges dominate, might be rotated
    return np.max(vertical_edges) > np.max(horizontal_edges) * 1.2

# Spanish ID keywords ↑ confidence when upright
KEYWORDS = ("DNI", "ESPAÑA", "ESP", "DOCUMENTO", "NACIONAL", "IDENTIDAD")

def _enhance_image_quality(img_bgr):
    """Apply CLAHE and sharpening to improve OCR quality"""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    # Apply sharpening kernel
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    # Convert back to BGR
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

def _ocr_score(img_bgr) -> float:
    """Return composite text-quality score with enhancement for low confidence."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # First attempt with original image
    data = pytesseract.image_to_data(
        gray, lang="spa+eng", output_type=pytesseract.Output.DICT
    )
    words = [w for w in data["text"] if w.strip()]
    if not words:
        return -1

    confs = [int(c) for c in data["conf"] if int(c) > 0]
    if not confs:
        return -1

    avg_conf = np.mean(confs)

    # If confidence is low, try with enhanced image
    if avg_conf < 75:
        enhanced_img = _enhance_image_quality(img_bgr)
        enhanced_gray = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)

        enhanced_data = pytesseract.image_to_data(
            enhanced_gray, lang="spa+eng", output_type=pytesseract.Output.DICT
        )
        enhanced_words = [w for w in enhanced_data["text"] if w.strip()]
        enhanced_confs = [int(c) for c in enhanced_data["conf"] if int(c) > 0]

        if enhanced_confs and np.mean(enhanced_confs) > avg_conf:
            words = enhanced_words
            avg_conf = np.mean(enhanced_confs)

    keyword_bonus = 25 * sum(k in " ".join(words).upper() for k in KEYWORDS)
    return avg_conf + 3*len(words) + keyword_bonus

def auto_rotate(path: str) -> str:
    """
    Brute-force OCR at 0/90/180/270 and keep best orientation
    Returns path to rotated image (may be original)
    """
    name = os.path.basename(path)

    # Always test all rotations for best OCR score
    # (Skip the heuristic check for now to ensure thorough testing)

    print(f"🔄 Testing rotations for: {name}")
    img   = cv2.imread(path)
    best  = img
    best_angle, best_score = 0, _ocr_score(img)
    print(f"   Angle 0°: Score={best_score:.1f}")

    for angle, rotflag in [(90,  cv2.ROTATE_90_COUNTERCLOCKWISE),
                           (180, cv2.ROTATE_180),
                           (270, cv2.ROTATE_90_CLOCKWISE)]:
        test = cv2.rotate(img, rotflag)
        score = _ocr_score(test)
        print(f"   Angle {angle}°: Score={score:.1f}")
        if score > best_score:
            best, best_score, best_angle = test, score, angle

    if best_angle:
        out = f"rot_{best_angle}_{name}"
        cv2.imwrite(out, best)
        print(f"🔄 Rotated {best_angle}° clockwise")
        return out
    else:
        print(f"📐 No rotation needed")
        return path
