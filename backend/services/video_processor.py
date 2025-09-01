import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import requests
from backend.models.schemas import VideoInfo, VideoStatus, UserVideoInfo
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

# Get logger from centralized configuration
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


def _is_cloud_environment() -> bool:
    """
    Check if the application is running in a cloud environment
    Returns True if running on Heroku or other cloud platforms
    """
    # DYNO and HEROKU_APP_NAME are Heroku-specific environment variables
    # PORT alone is not sufficient as it can be set locally
    return bool(os.getenv('DYNO') or os.getenv('HEROKU_APP_NAME'))

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

    def _get_video_info(self, url: str) -> Dict[str, Any]:

        video_id = None
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]

        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
    
        response = requests.get(oembed_url, headers=headers, timeout=5,proxies= {
                        'http': os.getenv('HTTP_PROXY'),
                        'https': os.getenv('HTTPS_PROXY'),
                    })
        response.raise_for_status()
                
        data = response.json()

        return data

    def _extract_video_info_and_transcript(self, url: str) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Extract both metadata and transcript in a single yt-dlp call
        Returns: (metadata_dict, transcript_string)
        """
        try:
            logger.info(f"Extracting video info and transcript in single call")

            metadata = self._get_video_info(url)
            logger.info(f"Extracted metadata: {metadata}")

            transcript = self._extract_transcript(url)
            
            return metadata, transcript
                
        except Exception as e:
            logger.error(f"Failed to extract video info and transcript: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Return fallback metadata
            fallback_metadata = {
                'title': 'Unknown',
                'description': '',
                'duration': None,
                'thumbnail': None,
                'uploader': '',
                'view_count': None,
                'upload_date': None,
            }
            return fallback_metadata, None

    
    
    def process_video(self, video_id: str, url: str, user_id: str, title: Optional[str] = None, description: Optional[str] = None):
        """
        Extract transcript from a YouTube video and associate with user
        """
        try:
            logger.info(f"Starting transcript extraction for video {video_id} by user {user_id}")
            
            # Associate video with user
            self._associate_video_with_user(video_id, user_id)
            
            # Extract both metadata and transcript in single call
            metadata = None
            transcript = None
            
            logger.info(f"Extracting video info and transcript")
            try:
                metadata, transcript = self._extract_video_info_and_transcript(url)
                title = metadata['title']
                logger.info(f"Extracted title: {title}")
            except Exception as e:
                logger.warning(f"Video info and transcript extraction failed: {e}")
                   
            # Update video status to transcribing
            self._update_video_status(video_id, VideoStatus.TRANSCRIBING, title, description, metadata)
            
            # Process transcript
            if transcript and len(transcript.strip()) > 0:
                logger.info(f"Transcript extraction successful for video {video_id}, length: {len(transcript)} characters")
                # Save transcript
                self._save_transcript(video_id, transcript)
                # Update status to completed
                self._update_video_status(video_id, VideoStatus.COMPLETED, title, description, metadata)
                logger.info(f"Transcript extraction completed for video {video_id}")
            else:
                logger.error(f"Transcript extraction failed for video {video_id} - no subtitles available")
                # Update status to failed
                self._update_video_status(video_id, VideoStatus.FAILED, title, description, metadata)
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
            logger.debug(f"Associated video {video_id} with user {user_id}")
    
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
        logger.debug(f"Getting videos for user {user_id}")
        
        if user_id not in self.user_videos:
            logger.debug(f"User {user_id} not found in user_videos mapping")
            return []
        
        videos = []
        for video_id in self.user_videos[user_id]:
            logger.debug(f"Checking video {video_id} for user {user_id}")
            if video_id in self.videos_metadata:
                video_data = self.videos_metadata[video_id]
                logger.debug(f"Video {video_id} metadata found")
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
                logger.warning(f"Could not extract YouTube video ID from URL")
                return None
            
            logger.debug(f"Attempting to get transcript for video ID: {youtube_video_id}")
            
            ytt_api = YouTubeTranscriptApi(proxy_config=WebshareProxyConfig(
            proxy_username=os.getenv('PROXY_USERNAME'),
                proxy_password=os.getenv('PROXY_PASSWORD'),
            ))
            
            # First, try to get all available languages to detect original language
           
            logger.debug("Getting list of available languages")
            transcript_list = ytt_api.list(youtube_video_id)

            language_code = 'en'

            for transcript in transcript_list:

                if transcript.language_code == 'en':
                    break
                else:
                    language_code = transcript.language_code
            
            raw_data = transcript_list.find_transcript([language_code]).fetch().to_raw_data()

            text_parts = []
            for segment in raw_data:
                if 'text' in segment:
                    text_parts.append(segment['text'])
            
            transcript_text = ' '.join(text_parts)
            
            return transcript_text
               
        except Exception as e:
            logger.error(f"Alternative transcript extraction failed: {e}")
            import traceback
            logger.error(f"Alternative method traceback: {traceback.format_exc()}")
            return None

    def _save_transcript(self, video_id: str, transcript: str):
        """Save transcript to file"""
        try:
            transcript_path = os.path.join(self.transcripts_dir, f"{video_id}.txt")
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            logger.debug(f"Saved transcript for {video_id}")
        except Exception as e:
            logger.error(f"Error saving transcript for {video_id}: {e}")
            raise

    def _download_and_parse_subtitle(self, subtitle_url: str) -> Optional[str]:
        """Download and parse subtitle from URL"""
        try:
            import requests
            response = requests.get(subtitle_url, timeout=30)
            if response.status_code == 200:
                logger.debug(f"_download_and_parse_subtitle status code: {response.status_code}")
                return self._parse_subtitle_content(response.text)
            else:
                logger.error(f"Failed to download subtitle: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading subtitle: {e}")
            return None