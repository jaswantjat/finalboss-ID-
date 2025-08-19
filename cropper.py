# cropper.py
import cv2, numpy as np, os
from east_detector import east_detector

def _create_manual_review_copy(path: str, reason: str) -> str:
    """Create a copy for manual review with reason logged"""
    import shutil
    name = os.path.basename(path)
    manual_path = f"manual_review_{name}"
    shutil.copy2(path, manual_path)

    # Log the reason
    with open("manual_review.log", "a") as f:
        f.write(f"{manual_path}: {reason}\n")

    print(f"⚠️  Routed to manual review: {reason}")
    return manual_path

def warp_card(path: str, out_w=856, out_h=540) -> str:
    img = cv2.imread(path)
    if img is None:
        return _create_manual_review_copy(path, "Could not read image file")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Try multiple edge detection strategies for different backgrounds
    strategies = [
        {"blur": (5,5), "canny": (75, 200), "name": "standard"},
        {"blur": (3,3), "canny": (50, 150), "name": "sensitive"},
        {"blur": (7,7), "canny": (100, 250), "name": "aggressive"}
    ]

    quad = None
    strategy_used = None

    for strategy in strategies:
        blur = cv2.GaussianBlur(gray, strategy["blur"], 0)
        edges = cv2.Canny(blur, strategy["canny"][0], strategy["canny"][1])
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02*peri, True)
            if len(approx) == 4:
                # Validate the quad is reasonable (not too small, not degenerate)
                area = cv2.contourArea(approx)
                img_area = img.shape[0] * img.shape[1]
                if area > img_area * 0.1:  # At least 10% of image area
                    quad = approx.reshape(4,2)
                    strategy_used = strategy["name"]
                    break

        if quad is not None:
            break

    if quad is None:
        return _create_manual_review_copy(path, "No 4-point contour found with any strategy")

    print(f"📐 Found 4-point contour using {strategy_used} strategy")

    # Order points tl,tr,br,bl
    s = quad.sum(axis=1)
    diff = np.diff(quad, axis=1).flatten()
    tl, br = quad[np.argmin(s)], quad[np.argmax(s)]
    tr, bl = quad[np.argmin(diff)], quad[np.argmax(diff)]
    pts_src = np.float32([tl,tr,br,bl])
    pts_dst = np.float32([[0,0],[out_w-1,0],[out_w-1,out_h-1],[0,out_h-1]])

    # Validate perspective transform
    try:
        M = cv2.getPerspectiveTransform(pts_src, pts_dst)
        warped = cv2.warpPerspective(img, M, (out_w, out_h))

        # Check if warped image is reasonable (not all black/white)
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        mean_intensity = np.mean(gray_warped)
        if mean_intensity < 10 or mean_intensity > 245:
            return _create_manual_review_copy(path, "Warped image has extreme intensity values")

        # Optional: Apply EAST-based deskew refinement
        skew_angle = east_detector.estimate_skew_angle(warped)
        if abs(skew_angle) > 1.0:  # Only correct if skew is significant
            print(f"🔧 Applying EAST-based deskew correction: {skew_angle:.1f}°")
            center = (out_w // 2, out_h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, -skew_angle, 1.0)
            warped = cv2.warpAffine(warped, rotation_matrix, (out_w, out_h),
                                  flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        out = f"crop_{os.path.basename(path)}"
        cv2.imwrite(out, warped)
        print(f"✂️  Cropped and warped to {out_w}x{out_h}")
        return out

    except cv2.error as e:
        return _create_manual_review_copy(path, f"Perspective transform failed: {str(e)}")
