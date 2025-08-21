from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.services.summarizer import Summarizer
from backend.services.video_processor import VideoProcessor

router = APIRouter()

# Initialize services (lazy loading for summarizer to avoid blocking startup)
summarizer = None
video_processor = VideoProcessor()

def get_summarizer():
    """Lazy load the summarizer to avoid blocking startup"""
    global summarizer
    if summarizer is None:
        summarizer = Summarizer()
    return summarizer

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

@router.post("/summarize", response_model=SummaryResponse)
async def summarize_video(request: SummaryRequest):
    """
    Generate a summary for a video transcript using Gemini
    """
    try:
        # Get the transcript
        transcript = video_processor.get_transcript(request.video_id)
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Check if summary is cached first
        summarizer_instance = get_summarizer()
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
            cached=is_cached
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.get("/styles")
async def get_summary_styles():
    """Get available summary styles"""
    try:
        styles = get_summarizer().get_available_styles()
        return {"styles": styles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting styles: {str(e)}")

@router.get("/cache-stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = get_summarizer().get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

