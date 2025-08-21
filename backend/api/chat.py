from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from backend.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    ChatMessage
)
from backend.services.chat_service import ChatService

router = APIRouter()

# Initialize chat service
chat_service = ChatService()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_video(request: ChatRequest):
    """
    Chat with the content of a processed video using RAG
    """
    try:
        # Convert conversation history to proper format
        conversation_history = []
        for msg in request.conversation_history:
            conversation_history.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ))
        
        # Get response from chat service
        response, sources = await chat_service.chat(
            video_id=request.video_id,
            message=request.message,
            conversation_history=conversation_history
        )
        
        # Add the new messages to conversation history
        conversation_history.append(ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now()
        ))
        conversation_history.append(ChatMessage(
            role="assistant",
            content=response,
            timestamp=datetime.now()
        ))
        
        return ChatResponse(
            video_id=request.video_id,
            response=response,
            sources=sources,
            conversation_history=conversation_history
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/{video_id}/history")
async def get_chat_history(video_id: str):
    """
    Get chat history for a specific video
    """
    try:
        history = chat_service.get_chat_history(video_id)
        return {"video_id": video_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/{video_id}/history")
async def clear_chat_history(video_id: str):
    """
    Clear chat history for a specific video
    """
    try:
        success = chat_service.clear_chat_history(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

