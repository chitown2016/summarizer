#!/usr/bin/env python3
"""
Test script to verify backend transcript extraction functionality
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_backend_health():
    """Test if the backend is running"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running. Please start it first:")
        print("   python start_backend.py")
        return False
    except Exception as e:
        print(f"❌ Error testing backend health: {e}")
        return False

def test_transcript_extraction():
    """Test transcript extraction"""
    print("\n🎬 Testing transcript extraction...")
    
    # Test video URL (the one we know works)
    test_url = "https://www.youtube.com/watch?v=wcD4S7mNbE8"
    
    # Prepare request
    payload = {
        "url": test_url,
        "title": "Test Video - Matt Hougan Interview",
        "description": "Testing transcript extraction functionality"
    }
    
    try:
        # Send extraction request
        print(f"📤 Sending extraction request for: {test_url}")
        response = requests.post(f"{API_URL}/process-video", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            video_id = result["video_id"]
            print(f"✅ Extraction started. Video ID: {video_id}")
            
            # Monitor extraction status
            return monitor_extraction(video_id)
        else:
            print(f"❌ Extraction request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing transcript extraction: {e}")
        return False

def monitor_extraction(video_id: str):
    """Monitor the extraction status of a video"""
    print(f"\n📊 Monitoring extraction for video: {video_id}")
    
    max_attempts = 30  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # Check status
            response = requests.get(f"{API_URL}/videos/{video_id}/status")
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data["status"]
                
                print(f"   Status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                if status == "completed":
                    print("✅ Transcript extraction completed successfully!")
                    return check_transcript(video_id)
                elif status == "failed":
                    print("❌ Transcript extraction failed")
                    return False
                elif status in ["pending", "transcribing"]:
                    # Continue monitoring
                    time.sleep(10)  # Wait 10 seconds before next check
                    attempt += 1
                else:
                    print(f"⚠️  Unknown status: {status}")
                    time.sleep(10)
                    attempt += 1
            elif response.status_code == 404:
                # Video not found yet, wait a bit
                print(f"   Video not found yet, waiting... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(5)
                attempt += 1
            else:
                print(f"❌ Status check failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return False
    
    print("⏰ Extraction timeout - taking too long")
    return False

def check_transcript(video_id: str):
    """Check if transcript was extracted successfully"""
    print(f"\n📄 Checking transcript for video: {video_id}")
    
    try:
        # Get video info
        response = requests.get(f"{API_URL}/videos/{video_id}")
        
        if response.status_code == 200:
            video_info = response.json()
            print(f"✅ Video info retrieved:")
            print(f"   Title: {video_info.get('title', 'Unknown')}")
            print(f"   Status: {video_info.get('status', 'Unknown')}")
            print(f"   Created: {video_info.get('created_at', 'Unknown')}")
            
            # Get transcript via API
            transcript_response = requests.get(f"{API_URL}/videos/{video_id}/transcript")
            
            if transcript_response.status_code == 200:
                transcript_data = transcript_response.json()
                transcript_content = transcript_data["transcript"]
                
                print(f"✅ Transcript retrieved via API:")
                print(f"   Length: {transcript_data['length']} characters")
                print(f"   Preview: {transcript_content[:200]}...")
                
                # Also check if file exists
                transcript_path = f"./data/transcripts/{video_id}.txt"
                if os.path.exists(transcript_path):
                    print(f"✅ Transcript file also exists: {transcript_path}")
                else:
                    print(f"⚠️  Transcript file not found: {transcript_path}")
                
                return True
            else:
                print(f"❌ Failed to get transcript via API: {transcript_response.status_code}")
                return False
        else:
            print(f"❌ Failed to get video info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking transcript: {e}")
        return False

def test_list_videos():
    """Test listing processed videos"""
    print("\n📋 Testing video listing...")
    
    try:
        response = requests.get(f"{API_URL}/videos")
        
        if response.status_code == 200:
            result = response.json()
            videos = result["videos"]
            print(f"✅ Found {len(videos)} processed videos")
            
            for video in videos:
                print(f"   - {video['id']}: {video['title']} ({video['status']})")
            
            return True
        else:
            print(f"❌ Failed to list videos: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error listing videos: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Backend Transcript Extraction Test")
    print("=" * 50)
    
    # Test 1: Backend health
    if not test_backend_health():
        return
    
    # Test 2: Transcript extraction
    if not test_transcript_extraction():
        print("\n❌ Transcript extraction test failed")
        return
    
    # Test 3: List videos
    test_list_videos()
    
    print("\n🎉 All tests completed!")
    print("\n💡 You can now:")
    print("   - View API docs at: http://localhost:8000/docs")
    print("   - Extract transcripts from any YouTube video")
    print("   - Get transcripts via API: GET /api/videos/{video_id}/transcript")

if __name__ == "__main__":
    main()
