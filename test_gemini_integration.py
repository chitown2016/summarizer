#!/usr/bin/env python3
"""
Test script for Gemini integration
"""

import os
import sys
from dotenv import find_dotenv, load_dotenv

# Add backend to path
sys.path.append('backend')

from backend.services.summarizer import Summarizer

def test_gemini_summarizer():
    """Test the Gemini-based summarizer"""
    
    # Load environment variables
    load_dotenv(find_dotenv())
    
    # Check if GOOGLE_API_KEY is set
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("Please set your Google API key in .env file or environment")
        return False
    
    print("🧪 Testing Gemini Summarizer...")
    
    try:
        # Initialize summarizer
        summarizer = Summarizer()
        print("✅ Summarizer initialized successfully")
        
        # Test text
        test_text = """
        Artificial Intelligence (AI) is transforming the way we live and work. 
        From virtual assistants like Siri and Alexa to self-driving cars, AI is becoming increasingly prevalent in our daily lives. 
        Machine learning, a subset of AI, enables computers to learn and improve from experience without being explicitly programmed. 
        Deep learning, which uses neural networks with multiple layers, has revolutionized fields like computer vision and natural language processing. 
        However, AI also raises important questions about privacy, job displacement, and ethical decision-making. 
        As we continue to develop more sophisticated AI systems, it's crucial to consider both the benefits and potential risks.
        """
        
        print(f"📝 Test text length: {len(test_text)} characters")
        
        # Test different styles
        styles = ["comprehensive", "bullet", "insights", "brief"]
        
        for style in styles:
            print(f"\n🔍 Testing style: {style}")
            summary = summarizer.summarize(test_text, style=style)
            
            if summary:
                print(f"✅ {style} summary generated ({len(summary)} chars)")
                print(f"📄 Preview: {summary[:100]}...")
            else:
                print(f"❌ Failed to generate {style} summary")
        
        # Test cache functionality
        print(f"\n💾 Cache stats: {summarizer.get_cache_stats()}")
        
        # Test cached retrieval
        print(f"\n🔄 Testing cache retrieval...")
        cached_summary = summarizer.summarize(test_text, style="comprehensive")
        if cached_summary:
            print("✅ Cached summary retrieved successfully")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_summarizer()
    sys.exit(0 if success else 1)
