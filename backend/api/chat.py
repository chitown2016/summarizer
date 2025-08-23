from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from backend.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    ChatMessage
)
from pydantic import BaseModel
from backend.services.chat_service import ChatService
from backend.middleware.auth import get_current_active_user
from backend.models.auth import User

router = APIRouter()

# Initialize chat service (lazy loading)
chat_service = None

def get_chat_service(user_id: str = None):
    """Lazy load the chat service to avoid blocking startup"""
    global chat_service
    if chat_service is None:
        chat_service = ChatService(user_id=user_id)
    elif user_id and chat_service.user_id != user_id:
        # Update user_id if different
        chat_service.set_user_id(user_id)
    return chat_service

@router.post("/chat", response_model=ChatResponse)
async def chat_with_video(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat with the content of a processed video using RAG
    """
    try:
        # Get chat service with user context
        chat_service_instance = get_chat_service(current_user.id)
        
        # Check API key availability
        if not chat_service_instance.has_api_key():
            raise HTTPException(
                status_code=400, 
                detail="No API key available. Please add an OpenAI API key in your profile settings."
            )
        
        # Convert conversation history to proper format
        conversation_history = []
        for msg in request.conversation_history:
            conversation_history.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ))
        
        # Get response from chat service
        response, sources = await chat_service_instance.chat(
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/api-key-status")
async def get_chat_api_key_status(current_user: User = Depends(get_current_active_user)):
    """Check API key availability for chat"""
    try:
        chat_service_instance = get_chat_service(current_user.id)
        has_key = chat_service_instance.has_api_key()
        source = chat_service_instance.get_api_key_source()
        
        if has_key:
            message = f"API key available from {source}"
        else:
            message = "No API key found. Please add an OpenAI API key in your profile settings."
        
        return {
            "has_api_key": has_key,
            "api_key_source": source,
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking API key status: {str(e)}")

@router.get("/chat/{video_id}/history")
async def get_chat_history(
    video_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get chat history for a specific video
    """
    try:
        history = get_chat_service(current_user.id).get_chat_history(video_id)
        return {"video_id": video_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/{video_id}/history")
async def clear_chat_history(
    video_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear chat history for a specific video
    """
    try:
        success = get_chat_service(current_user.id).clear_chat_history(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

