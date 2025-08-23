from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class VideoStatus(str, Enum):
    PENDING = "pending"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoProcessRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None

class VideoInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    status: VideoStatus
    created_at: datetime
    updated_at: datetime

class UserVideoInfo(VideoInfo):
    """Video info with user-specific data"""
    user_requested_at: datetime
    user_id: str

class VideoProcessResponse(BaseModel):
    video_id: str
    status: VideoStatus
    message: str

class SummaryRequest(BaseModel):
    video_id: str
    max_length: Optional[int] = 500
    style: Optional[str] = "concise"  # concise, detailed, bullet_points

class SummaryResponse(BaseModel):
    video_id: str
    summary: str
    word_count: int
    generated_at: datetime

class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    video_id: str
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    video_id: str
    response: str
    sources: List[Dict[str, Any]]
    conversation_history: List[ChatMessage]

class VideoListResponse(BaseModel):
    videos: List[VideoInfo]
    total: int

class UserVideoListResponse(BaseModel):
    videos: List[UserVideoInfo]
    total: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

