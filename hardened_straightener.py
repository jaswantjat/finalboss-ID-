#!/usr/bin/env python3
"""
Production-Ready Hardened Auto-Straightener
Robust orientation detection and skew correction for ID documents
"""

import cv2
import numpy as np
from PIL import Image, ImageOps
import pytesseract
import logging
import time
from typing import Tuple, Dict, Any, Optional
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance for performance
_orientation_model = None

def _get_orientation_model():
    """Get or initialize the PaddleOCR orientation model"""
    global _orientation_model
    if _orientation_model is None:
        try:
            from paddleocr import DocImgOrientationClassification
            logger.info("Loading PaddleOCR orientation model...")
            _orientation_model = DocImgOrientationClassification(model_name="PP-LCNet_x1_0_doc_ori", device="cpu", enable_mkldnn=True)
            logger.info("PaddleOCR orientation model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load PaddleOCR model: {e}")
            _orientation_model = None
    return _orientation_model

class HardenedOrientationDetector:
    """Production-ready orientation detection using PaddleOCR CNN classifier"""
    
    def __init__(self):
        # Lazy-load the model on first use to avoid import-time failures
        self.model = None
        self.confidence_threshold = 0.6
        
    def detect_orientation(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Detect document orientation using PaddleOCR CNN classifier
        
        Args:
            img: Input image as numpy array (BGR format)
            
        Returns:
            Dict with angle, confidence, method, and fallback info
        """
        try:
            if self.model is None:
                # Try to initialize now (lazy)
                self.model = _get_orientation_model()
            if self.model is None:
                logger.warning("PaddleOCR model not available, falling back to Tesseract OSD")
                return self._tesseract_osd_fallback(img)
            
            # Convert BGR to RGB for PaddleOCR
            if len(img.shape) == 3:
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                rgb_img = img
            
            # Get prediction from PaddleOCR
            pred = self.model.predict([rgb_img])[0]

            # PaddleOCR returns a dict-like object with label_names and scores
            angle = int(pred["label_names"][0])
            confidence = float(pred["scores"][0])
            
            logger.info(f"PaddleOCR orientation: {angle}° (confidence: {confidence:.3f})")
            
            # Check confidence and use fallback if needed
            if confidence < self.confidence_threshold:
                logger.warning(f"Low confidence ({confidence:.3f}), using Tesseract OSD fallback")
                fallback_result = self._tesseract_osd_fallback(img)
                
                # If fallback agrees or has higher confidence, use it
                if fallback_result["confidence"] > confidence:
                    return fallback_result
            
            return {
                "angle": angle,
                "confidence": confidence,
                "method": "paddleocr",
                "fallback_used": False
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR orientation detection failed: {e}")
            return self._tesseract_osd_fallback(img)
    
    def _tesseract_osd_fallback(self, img: np.ndarray) -> Dict[str, Any]:
        """Robust Tesseract OSD fallback with preprocessing"""
        try:
            # Preprocess image for better OSD results
            processed_img = self._preprocess_for_ocr(img)

            # Use Tesseract OSD with proper PSM mode
            osd = pytesseract.image_to_osd(
                processed_img,
                config="--psm 0 -c min_characters_to_try=10",
                output_type=pytesseract.Output.DICT
            )

            angle = int(osd.get('rotate', 0))
            confidence = float(osd.get('orientation_conf', 0)) / 100.0  # Convert to 0-1 range

            logger.info(f"Tesseract OSD orientation: {angle}° (confidence: {confidence:.3f})")

            # If OSD confidence is still low, try geometry fallback
            if confidence < 0.5:
                logger.warning("Low OSD confidence, trying geometry fallback")
                geometry_result = self._geometry_fallback(img)
                if geometry_result["confidence"] > confidence:
                    return geometry_result

            return {
                "angle": angle,
                "confidence": confidence,
                "method": "tesseract_osd",
                "fallback_used": True
            }

        except Exception as e:
            logger.error(f"Tesseract OSD fallback failed: {e}")
            return self._geometry_fallback(img)

    def _preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Upsample to ~300-400 DPI equivalent if image is small
        height, width = gray.shape
        if height < 800 or width < 800:
            scale_factor = max(800 / height, 800 / width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Adaptive thresholding for better text detection
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)

        return binary

    def _geometry_fallback(self, img: np.ndarray) -> Dict[str, Any]:
        """Geometry-based orientation detection for low-text images"""
        try:
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()

            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Hough line detection
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

            if lines is not None and len(lines) > 0:
                angles = []
                # Handle both HoughLines (rho, theta) and HoughLinesP (x1,y1,x2,y2) formats robustly
                for entry in lines[:20]:  # Use top 20 lines
                    vals = entry[0] if isinstance(entry, (list, tuple, np.ndarray)) else entry
                    # Convert to flat list
                    if isinstance(vals, np.ndarray):
                        vals = vals.flatten().tolist()
                    elif isinstance(vals, (list, tuple)):
                        vals = list(vals)
                    else:
                        continue

                    angle = None
                    if len(vals) >= 2 and len(vals) < 4:
                        # Standard HoughLines: [rho, theta]
                        rho, theta = float(vals[0]), float(vals[1])
                        angle = np.degrees(theta) - 90.0
                    elif len(vals) >= 4:
                        # Probabilistic HoughLinesP: [x1,y1,x2,y2]
                        x1, y1, x2, y2 = map(float, vals[:4])
                        angle = np.degrees(np.arctan2((y2 - y1), (x2 - x1)))
                    else:
                        continue

                    # Bucket angle to 0/90/180/270
                    if angle is not None:
                        a = ((angle + 360.0) % 360.0)  # normalize to [0,360)
                        if a <= 45 or a > 315:
                            angles.append(0)
                        elif 45 < a <= 135:
                            angles.append(90)
                        elif 135 < a <= 225:
                            angles.append(180)
                        else:
                            angles.append(270)

                if angles:
                    # Find most common angle
                    angle_counts = {0: 0, 90: 0, 180: 0, 270: 0}
                    for angle in angles:
                        angle_counts[angle] += 1

                    best_angle = max(angle_counts, key=angle_counts.get)
                    confidence = angle_counts[best_angle] / len(angles)

                    logger.info(f"Geometry orientation: {best_angle}° (confidence: {confidence:.3f})")

                    return {
                        "angle": best_angle,
                        "confidence": confidence,
                        "method": "geometry",
                        "fallback_used": True
                    }

            # If no lines found, assume no rotation needed
            return {
                "angle": 0,
                "confidence": 0.3,
                "method": "geometry_default",
                "fallback_used": True
            }

        except Exception as e:
            logger.error(f"Geometry fallback failed: {e}")
            return {
                "angle": 0,
                "confidence": 0.1,
                "method": "default",
                "fallback_used": True
            }
            
        except Exception as e:
            logger.error(f"Tesseract OSD fallback failed: {e}")
            return {
                "angle": 0,
                "confidence": 0.0,
                "method": "error",
                "fallback_used": True,
                "error": str(e)
            }

class HardenedSkewCorrector:
    """Fine skew correction using Hough line detection"""
    
    def __init__(self):
        self.max_skew_angle = 5.0  # Maximum skew angle to correct (degrees)
        self.min_skew_threshold = 0.3  # Minimum angle to apply correction
        
    def detect_skew_angle(self, img: np.ndarray) -> Tuple[float, float]:
        """
        Detect fine skew angle using Hough line detection
        
        Args:
            img: Input image as numpy array
            
        Returns:
            Tuple of (skew_angle, confidence)
        """
        try:
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Adaptive thresholding
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 10
            )
            
            # Morphological closing to connect text lines
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
            closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Detect lines using HoughLinesP
            lines = cv2.HoughLinesP(
                closed, 1, np.pi/180, threshold=100,
                minLineLength=50, maxLineGap=10
            )
            
            if lines is None or len(lines) == 0:
                return 0.0, 0.0
            
            # Calculate angles of detected lines
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 != x1:  # Avoid division by zero
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    # Normalize angle to [-90, 90] range
                    if angle > 45:
                        angle -= 90
                    elif angle < -45:
                        angle += 90
                    angles.append(angle)
            
            if not angles:
                return 0.0, 0.0
            
            # Use robust median to get dominant angle
            angles = np.array(angles)
            median_angle = np.median(angles)
            
            # Calculate confidence based on consistency of angles
            angle_std = np.std(angles)
            confidence = max(0.0, 1.0 - angle_std / 10.0)  # Higher std = lower confidence
            
            # Only return significant angles
            if abs(median_angle) > self.max_skew_angle:
                return 0.0, 0.0
            
            return median_angle, confidence
            
        except Exception as e:
            logger.error(f"Skew detection failed: {e}")
            return 0.0, 0.0
    
    def correct_skew(self, img: np.ndarray, angle: Optional[float] = None) -> Tuple[np.ndarray, float]:
        """
        Correct skew in image
        
        Args:
            img: Input image
            angle: Skew angle to correct (if None, will detect automatically)
            
        Returns:
            Tuple of (corrected_image, applied_angle)
        """
        if angle is None:
            angle, confidence = self.detect_skew_angle(img)
            logger.info(f"Detected skew: {angle:.2f}° (confidence: {confidence:.3f})")
        
        # Only apply correction if angle is significant
        if abs(angle) < self.min_skew_threshold:
            return img, 0.0
        
        # Apply rotation
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        
        # Calculate new image size to avoid cropping
        cos_angle = abs(rotation_matrix[0, 0])
        sin_angle = abs(rotation_matrix[0, 1])
        new_w = int((h * sin_angle) + (w * cos_angle))
        new_h = int((h * cos_angle) + (w * sin_angle))
        
        # Adjust translation
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]
        
        # Apply rotation
        corrected = cv2.warpAffine(
            img, rotation_matrix, (new_w, new_h),
            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        
        logger.info(f"Applied skew correction: {angle:.2f}°")
        return corrected, angle

class HardenedStraightener:
    """Complete hardened straightening pipeline"""
    
    def __init__(self):
        self.orientation_detector = HardenedOrientationDetector()
        self.skew_corrector = HardenedSkewCorrector()
    
    def straighten_image(self, image_input) -> Dict[str, Any]:
        """
        Complete straightening pipeline: EXIF -> Orientation -> Skew correction
        
        Args:
            image_input: PIL Image, numpy array, or file path
            
        Returns:
            Dict with straightened image and processing metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Handle input and fix EXIF orientation
            if isinstance(image_input, str):
                # File path
                pil_img = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                # PIL Image
                pil_img = image_input
            elif isinstance(image_input, np.ndarray):
                # Numpy array - convert to PIL
                if len(image_input.shape) == 3:
                    pil_img = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
                else:
                    pil_img = Image.fromarray(image_input)
            else:
                raise ValueError(f"Unsupported input type: {type(image_input)}")
            
            # Apply EXIF orientation and convert to RGB
            pil_img = ImageOps.exif_transpose(pil_img).convert("RGB")
            logger.info("Applied EXIF orientation correction")
            
            # Convert to OpenCV format for processing
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # Step 2: Coarse orientation detection (0/90/180/270)
            orientation_result = self.orientation_detector.detect_orientation(cv_img)
            angle = orientation_result["angle"]
            
            if angle != 0:
                if angle == 90:
                    cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif angle == 180:
                    cv_img = cv2.rotate(cv_img, cv2.ROTATE_180)
                elif angle == 270:
                    cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
                logger.info(f"Applied coarse rotation: {angle}°")
            
            # Step 3: Fine skew correction
            cv_img, skew_angle = self.skew_corrector.correct_skew(cv_img)
            
            # Convert back to PIL Image
            final_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "image": final_img,
                "processing_time": float(processing_time),
                "orientation": {
                    "angle_applied": int(angle),
                    "confidence": float(orientation_result["confidence"]),
                    "method": str(orientation_result["method"]),
                    "fallback_used": bool(orientation_result.get("fallback_used", False))
                },
                "skew_correction": {
                    "angle_applied": float(skew_angle),
                    "applied": bool(abs(skew_angle) > 0.3)
                }
            }
            
        except Exception as e:
            logger.error(f"Straightening failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": float(time.time() - start_time)
            }

# Global instance for performance
hardened_straightener = HardenedStraightener()
