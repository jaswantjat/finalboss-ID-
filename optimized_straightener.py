#!/usr/bin/env python3
"""
Optimized Straightener - Focus on accuracy and reliability
Based on test results, going back to basics with OCR-focused approach
"""

from PIL import Image
import cv2, pytesseract, numpy as np, os
import math

# Spanish ID keywords
KEYWORDS = ("DNI", "ESPAÑA", "ESP", "DOCUMENTO", "NACIONAL", "IDENTIDAD")

class OptimizedRotationDetector:
    """Optimized rotation detection focusing on OCR accuracy"""
    
    def __init__(self):
        self.debug = True
    
    def _enhance_for_ocr(self, img_bgr):
        """Enhanced preprocessing for better OCR"""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        
        return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
    
    def _get_comprehensive_ocr_score(self, img_bgr):
        """Comprehensive OCR scoring with multiple attempts"""
        scores = []
        
        # Try with original image
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        score1 = self._single_ocr_attempt(gray)
        scores.append(score1)
        
        # Try with enhanced image
        enhanced_img = self._enhance_for_ocr(img_bgr)
        enhanced_gray = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
        score2 = self._single_ocr_attempt(enhanced_gray)
        scores.append(score2)
        
        # Try with different binarization
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        score3 = self._single_ocr_attempt(binary)
        scores.append(score3)
        
        # Return the best score
        return max(scores, key=lambda x: x['total_score'])
    
    def _single_ocr_attempt(self, gray_img):
        """Single OCR attempt with detailed scoring"""
        try:
            # Get OCR data
            data = pytesseract.image_to_data(
                gray_img, 
                lang="spa+eng", 
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Extract valid words and confidences
            words = []
            confidences = []
            
            for i, word in enumerate(data["text"]):
                if word.strip():
                    conf = int(data["conf"][i])
                    if conf > 0:  # Only consider positive confidence
                        words.append(word.strip())
                        confidences.append(conf)
            
            if not words or not confidences:
                return {
                    'total_score': 0,
                    'avg_confidence': 0,
                    'word_count': 0,
                    'keyword_score': 0,
                    'high_conf_words': 0
                }
            
            # Calculate metrics
            avg_confidence = np.mean(confidences)
            word_count = len(words)
            
            # Count high confidence words (>70)
            high_conf_words = sum(1 for c in confidences if c > 70)
            
            # Keyword scoring
            all_text = " ".join(words).upper()
            keyword_matches = sum(1 for keyword in KEYWORDS if keyword in all_text)
            keyword_score = keyword_matches * 50  # Higher bonus for keywords
            
            # Length bonus for longer words (more likely to be real text)
            length_bonus = sum(len(word) for word in words if len(word) > 3) * 2
            
            # Calculate total score
            total_score = (
                avg_confidence * 0.4 +           # Base OCR confidence
                word_count * 5 +                 # Number of words found
                keyword_score +                  # Spanish ID keywords
                high_conf_words * 10 +           # High confidence words
                length_bonus                     # Longer words bonus
            )
            
            return {
                'total_score': total_score,
                'avg_confidence': avg_confidence,
                'word_count': word_count,
                'keyword_score': keyword_score,
                'high_conf_words': high_conf_words,
                'words': words
            }
            
        except Exception as e:
            if self.debug:
                print(f"      OCR error: {e}")
            return {
                'total_score': 0,
                'avg_confidence': 0,
                'word_count': 0,
                'keyword_score': 0,
                'high_conf_words': 0
            }
    
    def detect_best_rotation(self, img_path):
        """Detect best rotation using comprehensive OCR scoring"""
        img = cv2.imread(img_path)
        if img is None:
            return {"angle": 0, "confidence": 0, "method": "error"}
        
        results = {}
        
        # Test all 4 orientations
        for angle in [0, 90, 180, 270]:
            if angle == 0:
                test_img = img
            elif angle == 90:
                test_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif angle == 180:
                test_img = cv2.rotate(img, cv2.ROTATE_180)
            elif angle == 270:
                test_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            
            # Get comprehensive OCR score
            ocr_result = self._get_comprehensive_ocr_score(test_img)
            results[angle] = ocr_result
            
            if self.debug:
                print(f"   Angle {angle}°: Score={ocr_result['total_score']:.1f} "
                      f"(conf={ocr_result['avg_confidence']:.1f}, "
                      f"words={ocr_result['word_count']}, "
                      f"keywords={ocr_result['keyword_score']//50})")
        
        # Find best angle
        best_angle = max(results.keys(), key=lambda k: results[k]['total_score'])
        best_score = results[best_angle]['total_score']
        
        # Calculate confidence based on score difference
        scores = [results[k]['total_score'] for k in results.keys()]
        sorted_scores = sorted(scores, reverse=True)
        
        if len(sorted_scores) > 1:
            confidence = sorted_scores[0] - sorted_scores[1]
        else:
            confidence = best_score
        
        return {
            "best_angle": best_angle,
            "confidence": confidence,
            "all_results": results,
            "method": "optimized_ocr"
        }

class OptimizedSkewCorrector:
    """Optimized skew correction using projection profiles"""
    
    def __init__(self):
        self.debug = True
    
    def detect_skew_angle(self, img):
        """Detect skew using optimized projection profile method"""
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Binarize
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = 255 - binary  # Invert so text is white
        
        # Test range of angles with good resolution
        angles = np.arange(-8, 9, 0.2)  # -8 to +8 degrees, 0.2 degree steps
        variances = []
        
        for angle in angles:
            # Rotate image
            rotated = self._rotate_image(binary, angle)
            
            # Calculate horizontal projection
            h_projection = np.sum(rotated, axis=1)
            
            # Calculate variance (higher = better text line separation)
            variance = np.var(h_projection)
            variances.append(variance)
        
        # Find angle with maximum variance
        best_idx = np.argmax(variances)
        best_angle = angles[best_idx]
        max_variance = variances[best_idx]
        
        # Calculate confidence
        mean_variance = np.mean(variances)
        if mean_variance > 0:
            confidence = min(1.0, (max_variance - mean_variance) / mean_variance)
        else:
            confidence = 0
        
        return best_angle, confidence
    
    def _rotate_image(self, img, angle):
        """Rotate image by given angle"""
        if abs(angle) < 0.01:
            return img
        
        height, width = img.shape
        center = (width // 2, height // 2)
        
        # Create rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Apply rotation
        rotated = cv2.warpAffine(img, rotation_matrix, (width, height), 
                                flags=cv2.INTER_CUBIC, borderValue=0)
        
        return rotated
    
    def straighten_image(self, img, angle=None):
        """Straighten image by correcting skew"""
        if angle is None:
            if self.debug:
                print("🔍 Detecting skew angle...")
            angle, confidence = self.detect_skew_angle(img)
            
            if self.debug:
                print(f"📐 Detected skew: {angle:.2f}° (confidence: {confidence:.2f})")
        
        # Only correct if angle is significant
        if abs(angle) < 0.3:
            if self.debug:
                print("📐 No significant skew detected")
            return img, 0
        
        # Apply rotation
        if self.debug:
            print(f"🔧 Correcting skew by {angle:.2f}°")
        
        height, width = img.shape[:2]
        center = (width // 2, height // 2)
        
        # Create rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new dimensions to avoid cropping
        cos_angle = abs(rotation_matrix[0, 0])
        sin_angle = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_angle) + (width * cos_angle))
        new_height = int((height * cos_angle) + (width * sin_angle))
        
        # Adjust translation
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # Apply rotation
        straightened = cv2.warpAffine(
            img, rotation_matrix, (new_width, new_height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return straightened, angle

# Global instances
optimized_detector = OptimizedRotationDetector()
optimized_skew_corrector = OptimizedSkewCorrector()

def auto_rotate_optimized(path: str) -> str:
    """Optimized auto-rotation function"""
    name = os.path.basename(path)
    print(f"🎯 Optimized rotation detection for: {name}")
    
    result = optimized_detector.detect_best_rotation(path)
    best_angle = result["best_angle"]
    
    if best_angle == 0:
        print(f"📐 No rotation needed (confidence: {result['confidence']:.1f})")
        return path
    else:
        # Apply rotation
        img = cv2.imread(path)
        if best_angle == 90:
            rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif best_angle == 180:
            rotated = cv2.rotate(img, cv2.ROTATE_180)
        elif best_angle == 270:
            rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        
        out = f"optimized_rot_{best_angle}_{name}"
        cv2.imwrite(out, rotated)
        print(f"🔄 Rotated {best_angle}° (confidence: {result['confidence']:.1f})")
        return out

def complete_straightening(img_path: str) -> str:
    """Complete straightening: rotation + skew correction"""
    name = os.path.basename(img_path)
    print(f"🎯 Complete straightening for: {name}")
    
    # Step 1: Rotation detection
    rotated_path = auto_rotate_optimized(img_path)
    
    # Step 2: Skew correction
    img = cv2.imread(rotated_path)
    straightened, skew_angle = optimized_skew_corrector.straighten_image(img)
    
    # Save final result
    if abs(skew_angle) > 0.3:
        final_path = f"complete_straight_{name}"
        cv2.imwrite(final_path, straightened)
        print(f"✅ Complete straightening done: {final_path}")
        
        # Cleanup intermediate file
        if rotated_path != img_path and os.path.exists(rotated_path):
            os.remove(rotated_path)
        
        return final_path
    else:
        print(f"✅ Complete straightening done: {rotated_path}")
        return rotated_path

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python optimized_straightener.py <image_path>")
        sys.exit(1)
    
    result = complete_straightening(sys.argv[1])
    print(f"🎉 Final result: {result}")
