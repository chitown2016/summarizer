#!/usr/bin/env python3
"""
Working transcript extraction with proxy using youtube-transcript-api 1.2.2
"""

def test_proxy_transcript():
    """Test transcript extraction with proxy configuration"""
    print("🎬 Testing Transcript Extraction with Proxy")
    print("=" * 50)
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig
        
        # Create API instance with proxy configuration
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username="spsdiwcd",
                proxy_password="tc6oi1ejn932",
            )
        )
        
        video_id = 'vgiQlHmNE7E'
        print(f"🔍 Testing video ID: {video_id}")
        
        # Fetch transcript using the new API
        transcript = ytt_api.fetch(video_id)
        
        print(f"✅ Transcript fetched successfully!")
        print(f"Language: {transcript.language_code}")
        print(f"Is generated: {transcript.is_generated}")
        
        # Get the transcript data using the correct method
        transcript_data = transcript.snippets
        
        print(f"Number of segments: {len(transcript_data)}")
        
        # Show first few segments
        for i, segment in enumerate(transcript_data[:3]):
            print(f"\n📝 Segment {i+1}:")
            print(f"Time: {segment.start:.1f}s")
            print(f"Text: {segment.text}")
        
        # Get full text
        full_text = " ".join([segment.text for segment in transcript_data])
        print(f"\n📄 Full transcript length: {len(full_text)} characters")
        print(f"Preview: {full_text[:200]}...")
        
        return full_text, transcript_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return None, None

def test_raw_data():
    """Test getting raw data format"""
    print("\n🧪 Testing Raw Data Format")
    print("=" * 50)
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig
        
        # Create API instance with proxy configuration
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username="spsdiwcd",
                proxy_password="tc6oi1ejn932",
            )
        )
        
        video_id = 'vgiQlHmNE7E'
        transcript = ytt_api.fetch(video_id)
        
        # Get raw data (this is the format that matches the old API)
        raw_data = transcript.to_raw_data()
        
        print(f"✅ Raw data format:")
        print(f"Type: {type(raw_data)}")
        print(f"Length: {len(raw_data)}")
        
        # Show first few segments in raw format
        for i, segment in enumerate(raw_data[:3]):
            print(f"\n📝 Raw Segment {i+1}:")
            print(f"  {segment}")
        
        # Get full text from raw data
        full_text = " ".join([segment['text'] for segment in raw_data])
        print(f"\n📄 Full transcript length: {len(full_text)} characters")
        print(f"Preview: {full_text[:200]}...")
        
        return full_text, raw_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return None, None

def test_langchain_integration(raw_data):
    """Test integration with LangChain"""
    print("\n🧪 Testing LangChain Integration")
    print("=" * 50)
    
    try:
        from langchain.schema import Document
        
        if raw_data is None:
            print("❌ No transcript data available")
            return None
        
        # Create full text from raw data
        full_text = " ".join([segment['text'] for segment in raw_data])
        
        # Create a document for LangChain
        doc = Document(
            page_content=full_text,
            metadata={
                "source": "https://www.youtube.com/watch?v=wcD4S7mNbE8",
                "video_id": "vgiQlHmNE7E",
                "extraction_method": "proxy_api_v1.2.2"
            }
        )
        
        print(f"✅ Created LangChain document")
        print(f"Content length: {len(doc.page_content)} characters")
        print(f"Metadata: {doc.metadata}")
        
        return doc
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return None

if __name__ == "__main__":
    print("🧪 Working YouTube Transcript API 1.2.2 with Proxy")
    print("=" * 70)
    
    # Test proxy transcript extraction
    full_text, transcript_data = test_proxy_transcript()
    
    # Test raw data format
    raw_full_text, raw_data = test_raw_data()
    
    # Test LangChain integration
    if raw_data:
        doc = test_langchain_integration(raw_data)
    
    print(f"\n📋 Summary:")
    if full_text and raw_full_text:
        print("✅ Proxy transcript extraction successful!")
        print("✅ Both snippets and raw_data methods work")
        print("✅ You can now use this with your project")
        
        # Save the full text to a file
        try:
            with open('transcript_proxy_working.txt', 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"✅ Saved transcript to 'transcript_proxy_working.txt' ({len(full_text)} characters)")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
        
        print("\n💡 For your notebook, use:")
        print("   transcript = ytt_api.fetch(video_id)")
        print("   raw_data = transcript.to_raw_data()")
        print("   full_text = ' '.join([segment['text'] for segment in raw_data])")
    else:
        print("❌ Transcript extraction failed")
        print("💡 Check your proxy credentials and network connection")
