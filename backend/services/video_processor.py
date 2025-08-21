import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from backend.models.schemas import VideoInfo, VideoStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "./data")
        self.transcripts_dir = os.getenv("TRANSCRIPTS_DIR", "./data/transcripts")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)
        
        # Load video metadata
        self.metadata_file = os.path.join(self.data_dir, "videos.json")
        self.videos_metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load video metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save video metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.videos_metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _extract_youtube_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract YouTube video metadata using yt-dlp
        Returns: title, description, duration, thumbnail
        """
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'description': info.get('description', ''),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                }
                
        except Exception as e:
            logger.warning(f"Failed to extract YouTube metadata: {e}")
            return {
                'title': 'Unknown',
                'description': '',
                'duration': None,
                'thumbnail': None,
                'uploader': '',
                'view_count': None,
                'upload_date': None,
            }
    
    def process_video(self, video_id: str, url: str, title: Optional[str] = None, description: Optional[str] = None):
        """
        Extract transcript from a YouTube video
        """
        try:
            logger.info(f"Starting transcript extraction for {video_id}")
            
            # Extract YouTube metadata if title is not provided
            metadata = None
            if not title:
                logger.info(f"Extracting YouTube metadata for {url}")
                metadata = self._extract_youtube_metadata(url)
                title = metadata['title']
                if not description:
                    description = metadata['description']
                
                logger.info(f"Extracted title: {title}")
            
            # Update status to transcribing
            self._update_video_status(video_id, VideoStatus.TRANSCRIBING, title, description, metadata)
            
            # Extract transcript using proxy method
            transcript = self._extract_transcript_with_proxy(video_id, url)
            
            # Update status to completed
            self._update_video_status(video_id, VideoStatus.COMPLETED)
            
            logger.info(f"Transcript extraction completed for {video_id}")
            
        except Exception as e:
            logger.error(f"Error extracting transcript for {video_id}: {e}")
            self._update_video_status(video_id, VideoStatus.FAILED)
            raise
    
    def _extract_transcript_with_proxy(self, video_id: str, url: str) -> str:
        """
        Extract transcript using youtube-transcript-api
        First tries without proxy, then with proxy if needed
        """
        # Extract YouTube video ID from URL
        youtube_video_id = None
        if 'youtube.com/watch?v=' in url:
            youtube_video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            youtube_video_id = url.split('youtu.be/')[1].split('?')[0]
        else:
            youtube_video_id = video_id  # Assume it's already a YouTube ID
        
        # Try without proxy first (most reliable)
        try:
            logger.info(f"Attempting transcript extraction without proxy for {youtube_video_id}")
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Create API instance WITHOUT proxy
            ytt_api = YouTubeTranscriptApi()
            
            # Fetch transcript using YouTube video ID
            transcript = ytt_api.fetch(youtube_video_id)
            
            # Get raw data format
            raw_data = transcript.to_raw_data()
            
            # Extract full text
            full_text = ' '.join([segment['text'] for segment in raw_data])
            
            # Save transcript with the generated UUID (video_id), not YouTube ID
            transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            logger.info(f"Successfully extracted transcript for video {video_id} without proxy")
            return full_text
            
        except Exception as e:
            logger.warning(f"Direct transcript extraction failed for {youtube_video_id}: {e}")
            
            # Try with proxy as fallback
            try:
                logger.info(f"Attempting transcript extraction with proxy for {youtube_video_id}")
                from youtube_transcript_api.proxies import WebshareProxyConfig
                
                # Create API instance with proxy configuration
                ytt_api = YouTubeTranscriptApi(
                    proxy_config=WebshareProxyConfig(
                        proxy_username=os.getenv("PROXY_USERNAME", "spsdiwcd"),
                        proxy_password=os.getenv("PROXY_PASSWORD", "tc6oi1ejn932"),
                    )
                )
                
                # Fetch transcript using the proxy API
                transcript = ytt_api.fetch(youtube_video_id)
                
                # Get raw data format
                raw_data = transcript.to_raw_data()
                
                # Extract full text
                full_text = ' '.join([segment['text'] for segment in raw_data])
                
                # Save transcript with the generated UUID (video_id), not YouTube ID
                transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                
                logger.info(f"Successfully extracted transcript for video {video_id} with proxy")
                return full_text
                
            except Exception as proxy_error:
                logger.error(f"Both direct and proxy transcript extraction failed for {youtube_video_id}")
                logger.error(f"Direct error: {e}")
                logger.error(f"Proxy error: {proxy_error}")
                raise Exception(f"Failed to extract transcript: {e}")
    
    def _update_video_status(self, video_id: str, status: VideoStatus, title: Optional[str] = None, description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Update video status in metadata"""
        if video_id not in self.videos_metadata:
            self.videos_metadata[video_id] = {
                "id": video_id,
                "title": title or "Unknown",
                "description": description,
                "status": status.value,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add additional metadata if available
            if metadata:
                self.videos_metadata[video_id].update({
                    "duration": metadata.get("duration"),
                    "thumbnail": metadata.get("thumbnail"),
                    "uploader": metadata.get("uploader"),
                    "view_count": metadata.get("view_count"),
                    "upload_date": metadata.get("upload_date"),
                })
        else:
            self.videos_metadata[video_id]["status"] = status.value
            self.videos_metadata[video_id]["updated_at"] = datetime.now().isoformat()
            if title:
                self.videos_metadata[video_id]["title"] = title
            if description:
                self.videos_metadata[video_id]["description"] = description
            
            # Update additional metadata if provided
            if metadata:
                self.videos_metadata[video_id].update({
                    "duration": metadata.get("duration") or self.videos_metadata[video_id].get("duration"),
                    "thumbnail": metadata.get("thumbnail") or self.videos_metadata[video_id].get("thumbnail"),
                    "uploader": metadata.get("uploader") or self.videos_metadata[video_id].get("uploader"),
                    "view_count": metadata.get("view_count") or self.videos_metadata[video_id].get("view_count"),
                    "upload_date": metadata.get("upload_date") or self.videos_metadata[video_id].get("upload_date"),
                })
        
        self._save_metadata()
    
    def get_videos(self) -> List[VideoInfo]:
        """Get list of all videos"""
        videos = []
        for video_data in self.videos_metadata.values():
            videos.append(VideoInfo(
                id=video_data["id"],
                title=video_data["title"],
                description=video_data.get("description"),
                duration=video_data.get("duration"),
                thumbnail=video_data.get("thumbnail"),
                status=VideoStatus(video_data["status"]),
                created_at=datetime.fromisoformat(video_data["created_at"]),
                updated_at=datetime.fromisoformat(video_data["updated_at"])
            ))
        return videos
    
    def get_video(self, video_id: str) -> Optional[VideoInfo]:
        """Get specific video information"""
        if video_id in self.videos_metadata:
            video_data = self.videos_metadata[video_id]
            return VideoInfo(
                id=video_data["id"],
                title=video_data["title"],
                description=video_data.get("description"),
                duration=video_data.get("duration"),
                thumbnail=video_data.get("thumbnail"),
                status=VideoStatus(video_data["status"]),
                created_at=datetime.fromisoformat(video_data["created_at"]),
                updated_at=datetime.fromisoformat(video_data["updated_at"])
            )
        return None
    
    def get_video_status(self, video_id: str) -> Optional[VideoStatus]:
        """Get video status"""
        if video_id in self.videos_metadata:
            return VideoStatus(self.videos_metadata[video_id]["status"])
        return None
    
    def get_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript content for a video"""
        transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
        if os.path.exists(transcript_path):
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading transcript for {video_id}: {e}")
        return None
    
    def delete_video(self, video_id: str) -> bool:
        """Delete video and all associated data"""
        if video_id not in self.videos_metadata:
            return False
        
        try:
            # Remove from metadata
            del self.videos_metadata[video_id]
            self._save_metadata()
            
            # Remove transcript file
            transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
            if os.path.exists(transcript_path):
                os.remove(transcript_path)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {e}")
            return False
