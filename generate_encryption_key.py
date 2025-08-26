#!/usr/bin/env python3
"""
Generate a proper Fernet encryption key for API key encryption
"""

from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    print("Generated encryption key:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("\nAdd this to your .env file or environment variables.")
    return key.decode()

if __name__ == "__main__":
    generate_encryption_key()
