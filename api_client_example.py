#!/usr/bin/env python3
"""
Example API client for the ID Card Straightening API
Demonstrates how to use the API endpoints
"""

import requests
import base64
import json
from PIL import Image, ImageDraw, ImageFont
import io
import os

# API Configuration
API_BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a test ID card image"""
    img = Image.new('RGB', (400, 250), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    
    # Add border and text
    draw.rectangle([10, 10, 390, 240], outline='black', width=2)
    draw.text((30, 50), "DOCUMENTO NACIONAL", fill='black', font=font)
    draw.text((30, 80), "DE IDENTIDAD", fill='black', font=font)
    draw.text((30, 120), "DNI: 12345678X", fill='black', font=font)
    draw.text((30, 150), "ESPAÑA", fill='black', font=font)
    
    # Save test image
    img.save("test_id_card.jpg")
    
    # Create rotated version
    rotated = img.rotate(90, expand=True)
    rotated.save("test_id_card_rotated.jpg")
    
    print("✅ Test images created: test_id_card.jpg, test_id_card_rotated.jpg")

def test_health_check():
    """Test the health check endpoint"""
    print("\n🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Uptime: {data['uptime_seconds']:.1f} seconds")
            print(f"   Total requests: {data['total_requests']}")
            print(f"   Success rate: {data['success_rate']:.1f}%")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_straighten_api(image_path: str, return_format: str = "base64"):
    """Test the straighten endpoint"""
    print(f"\n🔄 Testing straighten endpoint with {image_path} (format: {return_format})...")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path, f, 'image/jpeg')}
            data = {'return_format': return_format}
            
            response = requests.post(f"{API_BASE_URL}/straighten", files=files, data=data)
        
        if response.status_code == 200:
            if return_format == "base64":
                result = response.json()
                print("✅ Processing successful!")
                print(f"   Processing time: {result['processing_time_seconds']:.3f}s")
                print(f"   Rotation applied: {result['rotation']['angle_applied']}°")
                print(f"   Rotation confidence: {result['rotation']['confidence']:.1f}")
                print(f"   Skew correction: {result['skew_correction']['angle_detected']:.2f}°")
                print(f"   OCR confidence: {result['ocr_confidence']:.1f}")
                print(f"   Keywords detected: {result['keywords_detected']}")
                
                # Save the result image
                if 'image_base64' in result:
                    image_data = base64.b64decode(result['image_base64'])
                    output_path = f"result_{os.path.basename(image_path)}"
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"   Result saved: {output_path}")
                
            elif return_format == "file":
                print("✅ Processing successful!")
                output_path = f"result_file_{os.path.basename(image_path)}"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"   Result file saved: {output_path}")
                
                # Try to get stats from headers
                if 'X-Processing-Stats' in response.headers:
                    print(f"   Processing stats: {response.headers['X-Processing-Stats']}")
        else:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ API call error: {e}")

def test_stats_endpoint():
    """Test the stats endpoint"""
    print("\n📊 Testing stats endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats retrieved successfully:")
            print(f"   Total requests: {data['total_requests']}")
            print(f"   Successful requests: {data['successful_requests']}")
            print(f"   Failed requests: {data['failed_requests']}")
            print(f"   Success rate: {data['success_rate_percent']:.1f}%")
            print(f"   Average processing time: {data['average_processing_time_seconds']:.3f}s")
        else:
            print(f"❌ Stats request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats request error: {e}")

def main():
    """Run all API tests"""
    print("🧪 ID Card Straightening API Client Test")
    print("=" * 50)
    
    # Create test images
    create_test_image()
    
    # Test health check
    test_health_check()
    
    # Test straightening with normal image (base64 format)
    test_straighten_api("test_id_card.jpg", "base64")
    
    # Test straightening with rotated image (file format)
    test_straighten_api("test_id_card_rotated.jpg", "file")
    
    # Test stats
    test_stats_endpoint()
    
    print("\n🎉 API testing complete!")
    print("\n📖 For interactive API documentation, visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
