#!/usr/bin/env python3
"""
Debug script to test transcript extraction directly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_transcript_extraction_direct():
    """Test transcript extraction directly without the API"""
    print("🔍 Testing transcript extraction directly...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig
        
        # Test video URL
        test_url = "https://www.youtube.com/watch?v=wcD4S7mNbE8"
        video_id = "wcD4S7mNbE8"
        
        print(f"📺 Testing with video: {video_id}")
        print(f"🔗 URL: {test_url}")
        
        # Get proxy credentials
        proxy_username = os.getenv("PROXY_USERNAME", "spsdiwcd")
        proxy_password = os.getenv("PROXY_PASSWORD", "tc6oi1ejn932")
        
        print(f"🔐 Using proxy: {proxy_username}")
        
        # Create API instance with proxy configuration
        print("🔄 Creating YouTubeTranscriptApi with proxy...")
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )
        
        print("📥 Fetching transcript...")
        # Fetch transcript using the proxy API
        transcript = ytt_api.fetch(video_id)
        
        print("✅ Transcript fetched successfully!")
        print(f"📄 Transcript type: {type(transcript)}")
        
        # Get raw data format
        print("🔄 Converting to raw data...")
        raw_data = transcript.to_raw_data()
        
        print(f"📊 Raw data type: {type(raw_data)}")
        print(f"📊 Raw data length: {len(raw_data)}")
        
        # Extract full text
        full_text = ' '.join([segment['text'] for segment in raw_data])
        
        print(f"📝 Full text length: {len(full_text)} characters")
        print(f"📝 Preview: {full_text[:200]}...")
        
        # Save transcript
        transcript_path = f"./debug_transcript_{video_id}.txt"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"💾 Transcript saved to: {transcript_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e)}")
        
        # Print more details about the error
        import traceback
        print("📋 Full traceback:")
        traceback.print_exc()
        
        return False

def test_video_processor_class():
    """Test the VideoProcessor class directly"""
    print("\n🔍 Testing VideoProcessor class...")
    
    try:
        from backend.services.video_processor import VideoProcessor
        
        processor = VideoProcessor()
        print("✅ VideoProcessor initialized")
        
        # Test with a simple video ID
        test_url = "https://www.youtube.com/watch?v=wcD4S7mNbE8"
        video_id = "wcD4S7mNbE8"
        
        print(f"📺 Testing extraction for: {video_id}")
        
        # Try to extract transcript
        transcript = processor._extract_transcript_with_proxy(video_id, test_url)
        
        print(f"✅ Transcript extracted successfully!")
        print(f"📝 Length: {len(transcript)} characters")
        print(f"📝 Preview: {transcript[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in VideoProcessor: {e}")
        print(f"❌ Error type: {type(e)}")
        
        import traceback
        print("📋 Full traceback:")
        traceback.print_exc()
        
        return False

def main():
    """Main debug function"""
    print("🐛 Transcript Extraction Debug")
    print("=" * 50)
    
    # Test 1: Direct API usage
    print("\n1️⃣ Testing direct YouTubeTranscriptApi usage...")
    if test_transcript_extraction_direct():
        print("✅ Direct API test passed")
    else:
        print("❌ Direct API test failed")
    
    # Test 2: VideoProcessor class
    print("\n2️⃣ Testing VideoProcessor class...")
    if test_video_processor_class():
        print("✅ VideoProcessor test passed")
    else:
        print("❌ VideoProcessor test failed")

if __name__ == "__main__":
    main()
