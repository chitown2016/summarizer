from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import os
from datetime import datetime
import uuid

from backend.models.schemas import (
    VideoProcessRequest, 
    VideoProcessResponse, 
    VideoInfo, 
    VideoListResponse,
    VideoStatus
)
from backend.services.video_processor import VideoProcessor

router = APIRouter()

# Initialize services
video_processor = VideoProcessor()

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Extract transcript from a YouTube video
    """
    try:
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        
        # Add transcript extraction to background tasks
        background_tasks.add_task(
            video_processor.process_video,
            video_id=video_id,
            url=str(request.url),
            title=request.title,
            description=request.description
        )
        
        return VideoProcessResponse(
            video_id=video_id,
            status=VideoStatus.PENDING,
            message="Transcript extraction started"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos", response_model=VideoListResponse)
async def list_videos():
    """
    List all processed videos
    """
    try:
        videos = video_processor.get_videos()
        return VideoListResponse(
            videos=videos,
            total=len(videos)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}", response_model=VideoInfo)
async def get_video(video_id: str):
    """
    Get information about a specific video
    """
    try:
        video = video_processor.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return video
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}/transcript")
async def get_transcript(video_id: str):
    """
    Get the transcript content for a specific video
    """
    try:
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
async def delete_video(video_id: str):
    """
    Delete a video and its transcript
    """
    try:
        success = video_processor.delete_video(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video and transcript deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}/status")
async def get_video_status(video_id: str):
    """
    Get the current processing status of a video
    """
    try:
        status = video_processor.get_video_status(video_id)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        return {"video_id": video_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"Error getting video status for {video_id}: {e}") # This line was commented out in the original file
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

