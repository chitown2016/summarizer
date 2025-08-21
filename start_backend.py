#!/usr/bin/env python3
"""
Simple script to start the backend server for testing
"""

import os
import sys
import subprocess
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    print("📋 Backend will be available at: http://localhost:8000")
    print("📋 API documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        # Change to the project directory
        os.chdir(Path(__file__).parent)
        
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "backend.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting backend: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")

if __name__ == "__main__":
    start_backend()
