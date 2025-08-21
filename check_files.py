#!/usr/bin/env python3
"""
Check if files were created
"""

import os
import json

def check_files():
    """Check if transcript files and metadata exist"""
    print("🔍 Checking files...")
    
    # Check data directory
    data_dir = "./data"
    if os.path.exists(data_dir):
        print(f"✅ Data directory exists: {data_dir}")
        print(f"📁 Contents: {os.listdir(data_dir)}")
    else:
        print(f"❌ Data directory not found: {data_dir}")
    
    # Check transcripts directory
    transcripts_dir = "./data/transcripts"
    if os.path.exists(transcripts_dir):
        print(f"✅ Transcripts directory exists: {transcripts_dir}")
        files = os.listdir(transcripts_dir)
        print(f"📁 Transcript files: {files}")
        
        # Check each transcript file
        for file in files:
            file_path = os.path.join(transcripts_dir, file)
            size = os.path.getsize(file_path)
            print(f"   📄 {file}: {size} bytes")
    else:
        print(f"❌ Transcripts directory not found: {transcripts_dir}")
    
    # Check metadata file
    metadata_file = "./data/videos.json"
    if os.path.exists(metadata_file):
        print(f"✅ Metadata file exists: {metadata_file}")
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            print(f"📊 Metadata contains {len(metadata)} videos:")
            for video_id, video_data in metadata.items():
                print(f"   🎬 {video_id}: {video_data.get('title', 'Unknown')} - {video_data.get('status', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error reading metadata: {e}")
    else:
        print(f"❌ Metadata file not found: {metadata_file}")

if __name__ == "__main__":
    check_files()
