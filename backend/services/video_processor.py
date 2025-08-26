import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from backend.models.schemas import VideoInfo, VideoStatus, UserVideoInfo

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
        
        # Load user-video relationships
        self.user_videos_file = os.path.join(self.data_dir, "user_videos.json")
        self.user_videos = self._load_user_videos()
    
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
    
    def _load_user_videos(self) -> Dict[str, List[str]]:
        """Load user-video relationships from file"""
        if os.path.exists(self.user_videos_file):
            try:
                with open(self.user_videos_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading user videos: {e}")
        return {}
    
    def _save_user_videos(self):
        """Save user-video relationships to file"""
        try:
            with open(self.user_videos_file, 'w') as f:
                json.dump(self.user_videos, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving user videos: {e}")
    
    def _extract_youtube_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract YouTube video metadata using yt-dlp
        Returns: title, description, duration, thumbnail
        """
        try:
            import yt_dlp
            logger.info(f"Attempting to extract metadata for {url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Extracting info with yt-dlp for {url}")
                info = ydl.extract_info(url, download=False)
                logger.info(f"Successfully extracted metadata for {url}")
                
                metadata = {
                    'title': info.get('title', 'Unknown'),
                    'description': info.get('description', ''),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                }
                logger.info(f"Extracted metadata: {metadata}")
                return metadata
                
        except Exception as e:
            logger.error(f"Failed to extract YouTube metadata for {url}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'title': 'Unknown',
                'description': '',
                'duration': None,
                'thumbnail': None,
                'uploader': '',
                'view_count': None,
                'upload_date': None,
            }
    
    def process_video(self, video_id: str, url: str, user_id: str, title: Optional[str] = None, description: Optional[str] = None):
        """
        Extract transcript from a YouTube video and associate with user
        """
        try:
            logger.info(f"Starting transcript extraction for {video_id} by user {user_id}")
            
            # Associate video with user
            self._associate_video_with_user(video_id, user_id)
            
            # Extract YouTube metadata if title is not provided
            metadata = None
            if not title:
                logger.info(f"Extracting YouTube metadata for {url}")
                metadata = self._extract_youtube_metadata(url)
                title = metadata['title']
                if not description:
                    description = metadata['description']
                
                logger.info(f"Extracted title: {title}")
            
            # Update video status to transcribing
            self._update_video_status(video_id, VideoStatus.TRANSCRIBING, title, description, metadata)
            
            # Extract transcript
            logger.info(f"Starting transcript extraction for {video_id}")
            transcript = self._extract_transcript(url)
            
            if transcript:
                logger.info(f"Transcript extraction successful for {video_id}, length: {len(transcript)}")
                # Save transcript
                self._save_transcript(video_id, transcript)
                # Update status to completed
                self._update_video_status(video_id, VideoStatus.COMPLETED, title, description, metadata)
                logger.info(f"Transcript extraction completed for {video_id}")
            else:
                logger.error(f"Transcript extraction failed for {video_id} - no subtitles available")
                # Update status to failed with specific reason
                self._update_video_status(video_id, VideoStatus.FAILED, title, description, metadata)
                logger.error(f"Transcript extraction failed for {video_id} - no subtitles available")
                # Save a placeholder transcript with error message
                error_message = "No transcript available for this video. This could be because:\n- The video doesn't have subtitles/closed captions\n- The subtitles are not publicly available\n- The video is private or restricted\n\nPlease try a different video with available subtitles."
                self._save_transcript(video_id, error_message)
                logger.info(f"Video {video_id} associated with user {user_id} and status set to FAILED")
                
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            self._update_video_status(video_id, VideoStatus.FAILED, title, description, metadata)
            # Save error message as transcript
            error_message = f"Error processing video: {str(e)}\n\nPlease try again or contact support if the problem persists."
            self._save_transcript(video_id, error_message)
            raise
    
    def _associate_video_with_user(self, video_id: str, user_id: str):
        """Associate a video with a user"""
        if user_id not in self.user_videos:
            self.user_videos[user_id] = []
        
        if video_id not in self.user_videos[user_id]:
            self.user_videos[user_id].append(video_id)
            self._save_user_videos()
            logger.info(f"Associated video {video_id} with user {user_id}")
    
    def _update_video_status(self, video_id: str, status: VideoStatus, title: Optional[str] = None, description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Update video status and metadata"""
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
        """Get list of all videos (admin function)"""
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
    
    def get_user_videos(self, user_id: str) -> List[UserVideoInfo]:
        """Get list of videos requested by a specific user"""
        logger.info(f"Getting videos for user {user_id}")
        logger.info(f"User videos mapping: {self.user_videos}")
        
        if user_id not in self.user_videos:
            logger.info(f"User {user_id} not found in user_videos mapping")
            return []
        
        videos = []
        for video_id in self.user_videos[user_id]:
            logger.info(f"Checking video {video_id} for user {user_id}")
            if video_id in self.videos_metadata:
                video_data = self.videos_metadata[video_id]
                logger.info(f"Video {video_id} metadata: {video_data}")
                videos.append(UserVideoInfo(
                    id=video_data["id"],
                    title=video_data["title"],
                    description=video_data.get("description"),
                    duration=video_data.get("duration"),
                    thumbnail=video_data.get("thumbnail"),
                    status=VideoStatus(video_data["status"]),
                    created_at=datetime.fromisoformat(video_data["created_at"]),
                    updated_at=datetime.fromisoformat(video_data["updated_at"]),
                    user_id=user_id,
                    user_requested_at=datetime.fromisoformat(video_data["created_at"])  # Use created_at as requested_at
                ))
            else:
                logger.warning(f"Video {video_id} not found in metadata for user {user_id}")
        
        # Sort by user_requested_at (most recent first)
        videos.sort(key=lambda x: x.user_requested_at, reverse=True)
        logger.info(f"Returning {len(videos)} videos for user {user_id}")
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
            
            # Remove from all user associations
            for user_id in list(self.user_videos.keys()):
                if video_id in self.user_videos[user_id]:
                    self.user_videos[user_id].remove(video_id)
            self._save_user_videos()
            
            # Remove transcript file
            transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
            if os.path.exists(transcript_path):
                os.remove(transcript_path)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {e}")
            return False
    
    def _extract_transcript(self, url: str) -> Optional[str]:
        """Extract transcript from YouTube video"""
        try:
            # Try without proxy first
            logger.info(f"Attempting transcript extraction without proxy for {url}")
            transcript = self._extract_transcript_without_proxy(url)
            
            if transcript:
                logger.info(f"Successfully extracted transcript for {url} without proxy")
                return transcript
            
            # If no transcript found, try with proxy
            logger.info(f"Attempting transcript extraction with proxy for {url}")
            transcript = self._extract_transcript_with_proxy(url)
            
            if transcript:
                logger.info(f"Successfully extracted transcript for {url} with proxy")
                return transcript
            
            # Try alternative methods
            logger.info(f"Attempting alternative transcript extraction methods for {url}")
            transcript = self._extract_transcript_alternative(url)
            
            if transcript:
                logger.info(f"Successfully extracted transcript using alternative method for {url}")
                return transcript
            
            logger.warning(f"No transcript found for {url} - video may not have subtitles")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting transcript for {url}: {e}")
            logger.error(f"Full error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _extract_transcript_alternative(self, url: str) -> Optional[str]:
        """Try alternative transcript extraction methods"""
        try:
            # Try using youtube-transcript-api as fallback
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Extract YouTube video ID from URL
            youtube_video_id = None
            if 'youtube.com/watch?v=' in url:
                youtube_video_id = url.split('v=')[1].split('&')[0]
            elif 'youtu.be/' in url:
                youtube_video_id = url.split('youtu.be/')[1].split('?')[0]
            else:
                logger.warning(f"Could not extract YouTube video ID from {url}")
                return None
            
            logger.info(f"Attempting to get transcript for video ID: {youtube_video_id}")
            
            # Create API instance (without proxy for now)
            ytt_api = YouTubeTranscriptApi()
            
            # Try to get transcript in different languages
            languages_to_try = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
            
            for lang in languages_to_try:
                try:
                    logger.info(f"Trying to get transcript in language: {lang}")
                    # Use the new API method: fetch() instead of get_transcript()
                    transcript = ytt_api.fetch(youtube_video_id, languages=[lang])
                    
                    if transcript:
                        logger.info(f"Successfully got transcript in {lang}")
                        # Get raw data format (compatible with old API format)
                        raw_data = transcript.to_raw_data()
                        
                        # Extract text from transcript segments
                        text_parts = []
                        for segment in raw_data:
                            if 'text' in segment:
                                text_parts.append(segment['text'])
                        
                        transcript_text = ' '.join(text_parts)
                        logger.info(f"Extracted {len(text_parts)} segments, total length: {len(transcript_text)}")
                        return transcript_text
                        
                except Exception as e:
                    logger.warning(f"Failed to get transcript in {lang}: {e}")
                    logger.warning(f"Full error for {lang}: {str(e)}")
                    continue
            
            # If no specific language worked, try without language specification
            try:
                logger.info("Trying to get transcript without language specification")
                transcript = ytt_api.fetch(youtube_video_id)
                
                if transcript:
                    logger.info("Successfully got transcript without language specification")
                    # Get raw data format
                    raw_data = transcript.to_raw_data()
                    
                    # Extract text from transcript segments
                    text_parts = []
                    for segment in raw_data:
                        if 'text' in segment:
                            text_parts.append(segment['text'])
                    
                    transcript_text = ' '.join(text_parts)
                    logger.info(f"Extracted {len(text_parts)} segments, total length: {len(transcript_text)}")
                    return transcript_text
                    
            except Exception as e:
                logger.warning(f"Failed to get transcript without language specification: {e}")
                logger.warning(f"Full error without language spec: {str(e)}")
            
            logger.warning(f"No transcript found for video ID: {youtube_video_id}")
            return None
            
        except Exception as e:
            logger.error(f"Alternative transcript extraction failed: {e}")
            logger.error(f"Full error details for alternative method: {str(e)}")
            import traceback
            logger.error(f"Alternative method traceback: {traceback.format_exc()}")
            return None
    
    def _extract_transcript_without_proxy(self, url: str) -> Optional[str]:
        """Extract transcript without using proxy"""
        try:
            import yt_dlp
            # Use yt-dlp to extract transcript
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Attempting to extract transcript for {url}")
                info = ydl.extract_info(url, download=False)
                
                # Check if subtitles are available
                if 'subtitles' in info or 'automatic_captions' in info:
                    logger.info(f"Subtitles found for {url}")
                    
                    # Try to get manual subtitles first
                    if 'subtitles' in info and info['subtitles']:
                        for lang, subs in info['subtitles'].items():
                            if lang.startswith('en'):
                                for sub in subs:
                                    if sub['ext'] == 'vtt':
                                        logger.info(f"Found manual subtitle: {sub['url']}")
                                        return self._download_and_parse_subtitle(sub['url'])
                    
                    # Try automatic captions if no manual subtitles
                    if 'automatic_captions' in info and info['automatic_captions']:
                        for lang, subs in info['automatic_captions'].items():
                            if lang.startswith('en'):
                                for sub in subs:
                                    if sub['ext'] == 'vtt':
                                        logger.info(f"Found automatic caption: {sub['url']}")
                                        return self._download_and_parse_subtitle(sub['url'])
                
                logger.warning(f"No subtitles found in yt-dlp info for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting transcript without proxy for {url}: {e}")
            return None
    
    def _extract_transcript_with_proxy(self, url: str) -> Optional[str]:
        """Extract transcript using proxy (if configured)"""
        try:
            import yt_dlp
            # Check if proxy is configured
            proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
            if not proxy_url:
                logger.warning("No proxy configured for transcript extraction")
                return None
            
            logger.info(f"Using proxy {proxy_url} for transcript extraction")
            
            # Use yt-dlp with proxy
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'proxy': proxy_url,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check if subtitles are available
                if 'subtitles' in info or 'automatic_captions' in info:
                    logger.info(f"Subtitles found with proxy for {url}")
                    
                    # Try to get manual subtitles first
                    if 'subtitles' in info and info['subtitles']:
                        for lang, subs in info['subtitles'].items():
                            if lang.startswith('en'):
                                for sub in subs:
                                    if sub['ext'] == 'vtt':
                                        logger.info(f"Found manual subtitle with proxy: {sub['url']}")
                                        return self._download_and_parse_subtitle(sub['url'])
                    
                    # Try automatic captions if no manual subtitles
                    if 'automatic_captions' in info and info['automatic_captions']:
                        for lang, subs in info['automatic_captions'].items():
                            if lang.startswith('en'):
                                for sub in subs:
                                    if sub['ext'] == 'vtt':
                                        logger.info(f"Found automatic caption with proxy: {sub['url']}")
                                        return self._download_and_parse_subtitle(sub['url'])
                
                logger.warning(f"No subtitles found with proxy for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting transcript with proxy for {url}: {e}")
            return None
    
    def _parse_subtitle_content(self, subtitle_content: str) -> str:
        """Parse subtitle content and extract text"""
        try:
            import re
            
            # Remove timestamp lines and empty lines
            lines = subtitle_content.split('\n')
            text_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines, timestamp lines, and subtitle index lines
                if (line and 
                    not re.match(r'^\d+$', line) and  # Index numbers
                    not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line)):  # Timestamps
                    text_lines.append(line)
            
            return ' '.join(text_lines)
            
        except Exception as e:
            logger.error(f"Error parsing subtitle content: {e}")
            return subtitle_content
    
    def _save_transcript(self, video_id: str, transcript: str):
        """Save transcript to file"""
        try:
            transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            logger.info(f"Saved transcript for {video_id}")
        except Exception as e:
            logger.error(f"Error saving transcript for {video_id}: {e}")
            raise

    def _download_and_parse_subtitle(self, subtitle_url: str) -> Optional[str]:
        """Download and parse subtitle from URL"""
        try:
            import requests
            response = requests.get(subtitle_url, timeout=30)
            if response.status_code == 200:
                logger.info(f"Successfully downloaded subtitle from {subtitle_url}")
                return self._parse_subtitle_content(response.text)
            else:
                logger.error(f"Failed to download subtitle: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading subtitle from {subtitle_url}: {e}")
            return None
