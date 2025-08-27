#!/usr/bin/env python3
"""
Script to clean up existing log files and test the new logging configuration.
"""

import os
import glob
import shutil
from pathlib import Path

def cleanup_existing_logs():
    """Clean up existing log files"""
    print("Cleaning up existing log files...")
    
    # Remove any existing app.log files
    log_files = glob.glob("*.log") + glob.glob("app.log")
    for log_file in log_files:
        try:
            os.remove(log_file)
            print(f"Removed: {log_file}")
        except FileNotFoundError:
            pass
    
    # Remove logs directory if it exists
    logs_dir = Path("logs")
    if logs_dir.exists():
        try:
            shutil.rmtree(logs_dir)
            print(f"Removed logs directory: {logs_dir}")
        except Exception as e:
            print(f"Error removing logs directory: {e}")
    
    print("Log cleanup completed.")

def test_logging_configuration():
    """Test the new logging configuration"""
    print("\nTesting new logging configuration...")
    
    # Import and setup logging
    from backend.utils.logging_config import setup_logging, get_logger
    
    # Setup logging
    setup_logging()
    
    # Test different loggers
    logger = get_logger("test")
    
    logger.debug("This is a debug message (should only appear in file)")
    logger.info("This is an info message (should appear in console and file)")
    logger.warning("This is a warning message (should appear in console and file)")
    logger.error("This is an error message (should appear in console, file, and error log)")
    
    print("Logging test completed. Check the logs/ directory for log files.")

if __name__ == "__main__":
    cleanup_existing_logs()
    test_logging_configuration()
    print("\nLogging configuration setup completed!")
