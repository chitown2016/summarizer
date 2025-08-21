#!/usr/bin/env python3
"""
Test transcript endpoint directly
"""

import requests

# Backend URL
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_transcript_endpoint(video_id):
    """Test the transcript endpoint directly"""
    print(f"📄 Testing transcript endpoint for video: {video_id}")
    
    try:
        # First check if video exists
        response = requests.get(f"{API_URL}/videos/{video_id}")
        print(f"📊 Video info response: {response.status_code}")
        
        if response.status_code == 200:
            video_info = response.json()
            print(f"✅ Video found: {video_info['title']} - {video_info['status']}")
        
        # Now try to get transcript
        transcript_response = requests.get(f"{API_URL}/videos/{video_id}/transcript")
        print(f"📄 Transcript response: {transcript_response.status_code}")
        
        if transcript_response.status_code == 200:
            transcript_data = transcript_response.json()
            print(f"✅ Transcript retrieved successfully!")
            print(f"📝 Length: {transcript_data['length']} characters")
            print(f"📝 Preview: {transcript_data['transcript'][:200]}...")
            return True
        else:
            print(f"❌ Transcript error: {transcript_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

if __name__ == "__main__":
    # Use the video ID from the last successful test
    video_id = "8e9a157d-fb02-46dd-9e92-f494231fba03"
    test_transcript_endpoint(video_id)
