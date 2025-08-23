from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
import os
from datetime import datetime
import uuid
import logging

from backend.models.schemas import (
    VideoProcessRequest, 
    VideoProcessResponse, 
    VideoInfo, 
    VideoListResponse,
    UserVideoListResponse,
    VideoStatus
)
from backend.services.video_processor import VideoProcessor
from backend.middleware.auth import get_current_user
from backend.models.auth import User

router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services
video_processor = VideoProcessor()

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Extract transcript from a YouTube video (requires authentication)
    """
    try:
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        
        # Add transcript extraction to background tasks with user_id
        background_tasks.add_task(
            video_processor.process_video,
            video_id=video_id,
            url=str(request.url),
            user_id=current_user.id,
            title=request.title,
            description=request.description
        )
        
        return VideoProcessResponse(
            video_id=video_id,
            status=VideoStatus.PENDING,
            message="Transcript extraction started"
        )
    
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos", response_model=UserVideoListResponse)
async def list_user_videos(current_user: User = Depends(get_current_user)):
    """
    List videos requested by the current user (requires authentication)
    """
    try:
        videos = video_processor.get_user_videos(current_user.id)
        return UserVideoListResponse(
            videos=videos,
            total=len(videos)
        )
    except Exception as e:
        logger.error(f"Error listing user videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}", response_model=VideoInfo)
async def get_video(
    video_id: str, 
    current_user: User = Depends(get_current_user)
):
    """
    Get information about a specific video (requires authentication and ownership)
    """
    try:
        # Check if user has access to this video
        user_videos = video_processor.get_user_videos(current_user.id)
        user_video_ids = [v.id for v in user_videos]
        
        if video_id not in user_video_ids:
            raise HTTPException(status_code=403, detail="Access denied to this video")
        
        video = video_processor.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return video
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}/transcript")
async def get_transcript(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the transcript content for a specific video (requires authentication and ownership)
    """
    try:
        # Check if user has access to this video
        user_videos = video_processor.get_user_videos(current_user.id)
        user_video_ids = [v.id for v in user_videos]
        
        if video_id not in user_video_ids:
            raise HTTPException(status_code=403, detail="Access denied to this video")
        
        transcript = video_processor.get_transcript(video_id)
        if transcript is None:
            raise HTTPException(status_code=404, detail=f"Transcript not found for video {video_id}")
        
        return {
            "video_id": video_id,
            "transcript": transcript,
            "length": len(transcript)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript for {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a video (requires authentication and ownership)
    """
    try:
        # Check if user has access to this video
        user_videos = video_processor.get_user_videos(current_user.id)
        user_video_ids = [v.id for v in user_videos]
        
        if video_id not in user_video_ids:
            raise HTTPException(status_code=403, detail="Access denied to this video")
        
        success = video_processor.delete_video(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {"message": "Video deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints (for future use)
@router.get("/admin/videos", response_model=VideoListResponse)
async def list_all_videos(current_user: User = Depends(get_current_user)):
    """
    List all videos (admin only - for future use)
    """
    # TODO: Add admin role check
    try:
        videos = video_processor.get_videos()
        return VideoListResponse(
            videos=videos,
            total=len(videos)
        )
    except Exception as e:
        logger.error(f"Error listing all videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

