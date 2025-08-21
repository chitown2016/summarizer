import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from backend.models.schemas import ChatMessage
from backend.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.chat_model = os.getenv("CHAT_MODEL", "mistral-7b-instruct")
        
        # Initialize chat model
        self._initialize_chat_model()
        
        # Chat history storage
        self.chat_history_dir = os.path.join(os.getenv("DATA_DIR", "./data"), "chat_history")
        os.makedirs(self.chat_history_dir, exist_ok=True)
    
    def _initialize_chat_model(self):
        """Initialize the chat model"""
        try:
            # For now, we'll use a simple approach with Hugging Face models
            # In production, you might want to use OpenAI API or other services
            
            # Check if we have OpenAI API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.use_openai = True
                import openai
                openai.api_key = openai_api_key
                logger.info("Using OpenAI API for chat")
            else:
                self.use_openai = False
                # Use local model (this is a simplified version)
                logger.info("Using local model for chat (simplified)")
                
        except Exception as e:
            logger.error(f"Error initializing chat model: {e}")
            self.use_openai = False
    
    async def chat(
        self, 
        video_id: str, 
        message: str, 
        conversation_history: List[ChatMessage] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Chat with video content using RAG
        """
        try:
            # Search for relevant content
            relevant_docs = self.vector_store.search(video_id, message, top_k=3)
            
            if not relevant_docs:
                return "I couldn't find any relevant information in the video content to answer your question.", []
            
            # Create context from relevant documents
            context = self._create_context(relevant_docs)
            
            # Generate response
            if self.use_openai:
                response = await self._generate_openai_response(message, context, conversation_history)
            else:
                response = await self._generate_local_response(message, context, conversation_history)
            
            # Save chat history
            self._save_chat_history(video_id, message, response, relevant_docs)
            
            return response, relevant_docs
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Sorry, I encountered an error while processing your request: {str(e)}", []
    
    def _create_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Create context string from relevant documents"""
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(f"Content: {doc['text']}")
            if doc.get('metadata', {}).get('start_time'):
                context_parts.append(f"Timestamp: {doc['metadata']['start_time']}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_openai_response(
        self, 
        message: str, 
        context: str, 
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """Generate response using OpenAI API"""
        try:
            import openai
            
            # Build conversation
            messages = [
                {
                    "role": "system",
                    "content": f"""You are a helpful assistant that answers questions about video content. 
                    Use the following context from the video to answer the user's question:
                    
                    {context}
                    
                    If the context doesn't contain enough information to answer the question, say so.
                    Be concise but informative."""
                }
            ]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return "I'm sorry, I couldn't generate a response at the moment."
    
    async def _generate_local_response(
        self, 
        message: str, 
        context: str, 
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """Generate response using local model (simplified)"""
        try:
            # This is a simplified version - in production you'd use a proper local model
            prompt = f"""Context from video:
{context}

User question: {message}

Answer based on the context above:"""
            
            # For now, return a simple response
            # In a real implementation, you'd use a local LLM here
            return f"Based on the video content, I found some relevant information. {context[:200]}... However, for better responses, consider using an API service like OpenAI."
            
        except Exception as e:
            logger.error(f"Error generating local response: {e}")
            return "I'm sorry, I couldn't generate a response at the moment."
    
    def _save_chat_history(
        self, 
        video_id: str, 
        user_message: str, 
        assistant_response: str, 
        sources: List[Dict[str, Any]]
    ):
        """Save chat history to file"""
        try:
            history_file = os.path.join(self.chat_history_dir, f"{video_id}.json")
            
            # Load existing history
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new messages
            history.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "assistant_response": assistant_response,
                "sources": sources
            })
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
    
    def get_chat_history(self, video_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a video"""
        try:
            history_file = os.path.join(self.chat_history_dir, f"{video_id}.json")
            
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
            
            return []
            
        except Exception as e:
            logger.error(f"Error loading chat history: {e}")
            return []
    
    def clear_chat_history(self, video_id: str) -> bool:
        """Clear chat history for a video"""
        try:
            history_file = os.path.join(self.chat_history_dir, f"{video_id}.json")
            
            if os.path.exists(history_file):
                os.remove(history_file)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
            return False

