from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from backend.services.summarizer import Summarizer
from backend.services.video_processor import VideoProcessor
from backend.middleware.auth import get_current_active_user
from backend.models.auth import User

router = APIRouter()

# Initialize services (lazy loading for summarizer to avoid blocking startup)
summarizers = {}  # Change from single instance to dict per user
video_processor = VideoProcessor()

def get_summarizer(user_id: Optional[str] = None):
    """Lazy load the summarizer to avoid blocking startup"""
    global summarizers
    if user_id not in summarizers:
        summarizers[user_id] = Summarizer(user_id=user_id)
    return summarizers[user_id]

class SummaryRequest(BaseModel):
    video_id: str
    style: Optional[str] = "comprehensive"

class SummaryResponse(BaseModel):
    video_id: str
    summary: str
    word_count: int
    original_length: int
    style: str
    cached: bool = False
    api_key_source: Optional[str] = None

class APIKeyStatusResponse(BaseModel):
    has_api_key: bool
    api_key_source: str
    message: str

@router.post("/summarize", response_model=SummaryResponse)
async def summarize_video(
    request: SummaryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a summary for a video transcript using Gemini
    """
    try:
        # Get logger from centralized configuration
        logger = logging.getLogger(__name__)
        logger.info(f"Summarize request for user: {current_user.id} (email: {current_user.email})")
        
        # Get the transcript
        transcript = video_processor.get_transcript(request.video_id)
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Get summarizer with user context
        summarizer_instance = get_summarizer(current_user.id)
        logger.info(f"Got summarizer instance for user {current_user.id}")
        
        # Check API key availability
        has_key = summarizer_instance.has_api_key()
        logger.info(f"API key check result: {has_key}")
        
        if not has_key:
            raise HTTPException(
                status_code=400, 
                detail="No API key available. Please add a Google API key in your profile settings."
            )
        
        # Check if summary is cached first
        cache_key = summarizer_instance._get_cache_key(transcript, request.style)
        cached_summary = summarizer_instance._load_from_cache(cache_key)
        is_cached = cached_summary is not None
        
        # Generate summary (will use cache if available)
        summary = summarizer_instance.summarize(transcript, style=request.style)
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        return SummaryResponse(
            video_id=request.video_id,
            summary=summary,
            word_count=len(summary.split()),
            original_length=len(transcript),
            style=request.style,
            cached=is_cached,
            api_key_source=summarizer_instance.get_api_key_source()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Get logger from centralized configuration
        logger = logging.getLogger(__name__)
        logger.error(f"Error in summarize_video: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.get("/api-key-status", response_model=APIKeyStatusResponse)
async def get_api_key_status(current_user: User = Depends(get_current_active_user)):
    """Check API key availability for the current user"""
    try:
        summarizer_instance = get_summarizer(current_user.id)
        has_key = summarizer_instance.has_api_key()
        source = summarizer_instance.get_api_key_source()
        
        if has_key:
            message = f"API key available from {source}"
        else:
            message = "No API key found. Please add a Google API key in your profile settings."
        
        return APIKeyStatusResponse(
            has_api_key=has_key,
            api_key_source=source,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking API key status: {str(e)}")

@router.post("/migrate-env-key")
async def migrate_environment_key(current_user: User = Depends(get_current_active_user)):
    """Migrate environment variable API key to user's database"""
    try:
        summarizer_instance = get_summarizer(current_user.id)
        success = summarizer_instance._migrate_env_key_to_db(current_user.id)
        
        if success:
            return {"message": "Successfully migrated environment API key to database"}
        else:
            raise HTTPException(
                status_code=400, 
                detail="No environment API key found or migration failed"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error migrating API key: {str(e)}")

@router.get("/styles")
async def get_summary_styles(current_user: User = Depends(get_current_active_user)):
    """Get available summary styles"""
    try:
        styles = get_summarizer(current_user.id).get_available_styles()
        return {"styles": styles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting styles: {str(e)}")

@router.get("/cache-stats")
async def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """Get cache statistics"""
    try:
        stats = get_summarizer(current_user.id).get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

