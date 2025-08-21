#!/usr/bin/env python3
"""
Test transcript extraction without proxy
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_without_proxy():
    """Test transcript extraction without proxy"""
    print("🔍 Testing transcript extraction WITHOUT proxy...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Test video URL
        test_url = "https://www.youtube.com/watch?v=wcD4S7mNbE8"
        video_id = "wcD4S7mNbE8"
        
        print(f"📺 Testing with video: {video_id}")
        print(f"🔗 URL: {test_url}")
        
        # Create API instance WITHOUT proxy
        print("🔄 Creating YouTubeTranscriptApi WITHOUT proxy...")
        ytt_api = YouTubeTranscriptApi()
        
        print("📥 Fetching transcript...")
        # Fetch transcript
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
        transcript_path = f"./transcript_no_proxy_{video_id}.txt"
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

def test_different_video():
    """Test with a different video that might have better transcript availability"""
    print("\n🔍 Testing with a different video...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Try a different video (TED talk - usually has good transcripts)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = "dQw4w9WgXcQ"
        
        print(f"📺 Testing with video: {video_id}")
        print(f"🔗 URL: {test_url}")
        
        # Create API instance WITHOUT proxy
        ytt_api = YouTubeTranscriptApi()
        
        print("📥 Fetching transcript...")
        transcript = ytt_api.fetch(video_id)
        
        print("✅ Transcript fetched successfully!")
        
        # Get raw data format
        raw_data = transcript.to_raw_data()
        full_text = ' '.join([segment['text'] for segment in raw_data])
        
        print(f"📝 Full text length: {len(full_text)} characters")
        print(f"📝 Preview: {full_text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with different video: {e}")
        return False

def main():
    """Main test function"""
    print("🐛 No-Proxy Transcript Extraction Test")
    print("=" * 50)
    
    # Test 1: Without proxy
    print("\n1️⃣ Testing without proxy...")
    if test_without_proxy():
        print("✅ No-proxy test passed")
    else:
        print("❌ No-proxy test failed")
    
    # Test 2: Different video
    print("\n2️⃣ Testing with different video...")
    if test_different_video():
        print("✅ Different video test passed")
    else:
        print("❌ Different video test failed")

if __name__ == "__main__":
    main()
