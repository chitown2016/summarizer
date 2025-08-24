#!/usr/bin/env python3
"""
Generate a proper Fernet encryption key for API key encryption
"""

from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a proper Fernet encryption key"""
    key = Fernet.generate_key()
    print(f"Generated Fernet encryption key: {key.decode()}")
    print(f"Key length: {len(key)} bytes")
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    
    return key.decode()

if __name__ == "__main__":
    generate_encryption_key()
