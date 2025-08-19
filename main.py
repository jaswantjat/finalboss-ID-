# main.py
import sys, os, straightener, cropper

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <image_path>")
        sys.exit(1)
    
    src = sys.argv[1]
    if not os.path.exists(src):
        print(f"Error: File '{src}' not found")
        sys.exit(1)
    
    print(f"🔄 Processing: {src}")
    rot_path = straightener.auto_rotate(src)
    crop_path = cropper.warp_card(rot_path)
    print("✔  Final image saved:", crop_path)
