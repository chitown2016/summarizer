#!/usr/bin/env python3
"""
Simple test to check backend API
"""

import requests
import json

# Backend URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_backend_health():
    """Test if the backend is running"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health status: {response.status_code}")
        print(f"Health response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check error: {e}")
        return False

def test_process_video():
    """Test video processing endpoint"""
    print("\n🎬 Testing video processing...")
    
    # Test video URL
    test_url = "https://www.youtube.com/watch?v=wcD4S7mNbE8"
    
    payload = {
        "url": test_url,
        "title": "Test Video",
        "description": "Testing transcript extraction"
    }
    
    try:
        print(f"📤 Sending request to: {API_URL}/process-video")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{API_URL}/process-video", json=payload)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {json.dumps(result, indent=2)}")
            return result.get("video_id")
        else:
            print(f"❌ Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def test_video_status(video_id):
    """Test video status endpoint"""
    if not video_id:
        return
    
    print(f"\n📊 Testing video status for: {video_id}")
    
    try:
        response = requests.get(f"{API_URL}/videos/{video_id}/status")
        
        print(f"📥 Status response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Status error: {response.text}")
            
    except Exception as e:
        print(f"❌ Status request error: {e}")

def main():
    """Main test function"""
    print("🧪 Simple Backend Test")
    print("=" * 30)
    
    # Test 1: Health
    if not test_backend_health():
        print("❌ Backend health check failed")
        return
    
    # Test 2: Process video
    video_id = test_process_video()
    
    # Test 3: Check status
    if video_id:
        test_video_status(video_id)

if __name__ == "__main__":
    main()
