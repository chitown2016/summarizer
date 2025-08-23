#!/usr/bin/env python3
"""
Start script for YouTube Transcript Extractor
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  FFmpeg not found. It's not required for transcript extraction, but may be needed for future features.")
    return True

def check_virtual_environment():
    """Check if running in a virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
        return True
    else:
        print("⚠️  Not running in virtual environment")
        print("   Consider creating one: python -m venv venv")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'backend.main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000',
            '--reload'
        ], env=env)
        
        print("✅ Backend server started on http://localhost:8000")
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def serve_frontend():
    """Serve the frontend using Python's built-in HTTP server"""
    print("🌐 Starting frontend server...")
    try:
        # Change to frontend directory
        frontend_dir = Path('frontend')
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return None
        
        # Start HTTP server
        process = subprocess.Popen([
            sys.executable, '-m', 'http.server', '3000'
        ], cwd=frontend_dir)
        
        print("✅ Frontend server started on http://localhost:3000")
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def wait_for_backend():
    """Wait for backend to be ready"""
    import requests
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        time.sleep(2)
        print("⏳ Waiting for backend...")
    
    print("❌ Backend failed to start")
    return False

def main():
    """Main startup function"""
    print("🎬 YouTube Transcript Extractor")
    print("=" * 40)
    
    # Check requirements
    if not check_python_version():
        return
    
    check_ffmpeg()
    check_virtual_environment()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Wait for backend to be ready
    if not wait_for_backend():
        backend_process.terminate()
        return
    
    # Start frontend
    frontend_process = serve_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    # Open browser
    print("🌐 Opening browser...")
    webbrowser.open('http://localhost:3000')
    
    print("\n🎉 Application started successfully!")
    print("📱 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the servers")
    
    try:
        # Keep the servers running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main()
