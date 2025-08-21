#!/usr/bin/env python3
"""
Check the new video that was just processed
"""

import requests
import time

# Backend URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def check_new_video():
    """Check the new video that was just processed"""
    video_id = "5e02a629-8eb4-4e8c-90e3-ef52e7750c5f"
    
    print(f"🔍 Checking new video: {video_id}")
    
    # Check status
    try:
        response = requests.get(f"{API_URL}/videos/{video_id}/status")
        if response.status_code == 200:
            result = response.json()
            status = result["status"]
            print(f"📊 Status: {status}")
            
            if status == "completed":
                print("✅ Video completed! Testing transcript...")
                
                # Test transcript endpoint
                transcript_response = requests.get(f"{API_URL}/videos/{video_id}/transcript")
                if transcript_response.status_code == 200:
                    transcript_data = transcript_response.json()
                    print(f"🎉 Transcript retrieved successfully!")
                    print(f"📝 Length: {transcript_data['length']} characters")
                    print(f"📝 Preview: {transcript_data['transcript'][:200]}...")
                    return True
                else:
                    print(f"❌ Transcript error: {transcript_response.status_code} - {transcript_response.text}")
                    return False
            else:
                print(f"⏳ Still processing: {status}")
                return False
        else:
            print(f"❌ Status error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_new_video()
