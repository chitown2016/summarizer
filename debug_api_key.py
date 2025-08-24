#!/usr/bin/env python3
"""
Debug script to test API key retrieval
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.auth_service import auth_service
from backend.services.summarizer import Summarizer

def test_api_key_retrieval():
    """Test API key retrieval for different users"""
    
    # Test with a known user ID from the database
    test_user_id = "64b7c667-e9a3-4d9d-a1a2-f8a1d1febaec"  # newuser1@mail.com
    
    print(f"Testing API key retrieval for user: {test_user_id}")
    
    # Test auth service directly
    print("\n1. Testing auth_service.get_user_default_api_key:")
    api_key_obj = auth_service.get_user_default_api_key(test_user_id, "google")
    print(f"Result: {api_key_obj}")
    
    if api_key_obj:
        print(f"API Key ID: {api_key_obj.id}")
        print(f"API Key Name: {api_key_obj.name}")
        print(f"API Key Provider: {api_key_obj.provider}")
        print(f"API Key (first 10 chars): {api_key_obj.api_key[:10] if api_key_obj.api_key else 'None'}...")
    
    # Test summarizer
    print("\n2. Testing Summarizer:")
    summarizer = Summarizer(user_id=test_user_id)
    print(f"Summarizer user_id: {summarizer.user_id}")
    
    has_key = summarizer.has_api_key()
    print(f"Has API key: {has_key}")
    
    source = summarizer.get_api_key_source()
    print(f"API key source: {source}")
    
    # Test with another user
    test_user_id2 = "2384bc46-265c-4238-9b21-f56c23d41bdd"  # test@example.com
    print(f"\n3. Testing with another user: {test_user_id2}")
    
    summarizer2 = Summarizer(user_id=test_user_id2)
    has_key2 = summarizer2.has_api_key()
    print(f"Has API key: {has_key2}")
    
    source2 = summarizer2.get_api_key_source()
    print(f"API key source: {source2}")

if __name__ == "__main__":
    test_api_key_retrieval()
