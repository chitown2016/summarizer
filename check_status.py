#!/usr/bin/env python3
"""
Check status of a specific video
"""

import requests
import time

# Backend URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def check_video_status(video_id):
    """Check status of a specific video"""
    print(f"📊 Checking status for video: {video_id}")
    
    try:
        response = requests.get(f"{API_URL}/videos/{video_id}/status")
        
        if response.status_code == 200:
            result = response.json()
            status = result["status"]
            print(f"✅ Status: {status}")
            return status
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def monitor_video(video_id, max_attempts=10):
    """Monitor video status until completion"""
    print(f"🔍 Monitoring video: {video_id}")
    
    for attempt in range(max_attempts):
        status = check_video_status(video_id)
        
        if status == "completed":
            print("🎉 Video processing completed!")
            return True
        elif status == "failed":
            print("❌ Video processing failed!")
            return False
        elif status in ["pending", "transcribing"]:
            print(f"⏳ Still processing... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(5)  # Wait 5 seconds
        else:
            print(f"⚠️  Unknown status: {status}")
            time.sleep(5)
    
    print("⏰ Timeout - processing taking too long")
    return False

if __name__ == "__main__":
    # Use the video ID from the last test
    video_id = "453afc71-6413-46d0-8bcd-9eb3090eeb48"
    monitor_video(video_id)
