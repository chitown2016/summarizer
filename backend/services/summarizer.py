import os
import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import find_dotenv, load_dotenv

from backend.services.auth_service import auth_service

logger = logging.getLogger(__name__)

class Summarizer:
    def __init__(self, user_id: Optional[str] = None):
        self.cache_dir = Path("data/summaries")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        load_dotenv(find_dotenv())
        
        # Store user_id for API key lookup
        self.user_id = user_id
        
        # Initialize Gemini with API key
        self.chat = self._initialize_gemini()
        
        # Create different prompt templates for different styles
        self.prompts = {
            "comprehensive": self._create_comprehensive_prompt(),
            "bullet": self._create_bullet_prompt(),
            "insights": self._create_insights_prompt(),
            "timeline": self._create_timeline_prompt(),
            "qa": self._create_qa_prompt(),
            "brief": self._create_brief_prompt()
        }
        
        logger.info("Summarizer initialized with Gemini 2.5 Flash")

    def _initialize_gemini(self) -> Optional[ChatGoogleGenerativeAI]:
        """Initialize Gemini with API key from database or environment"""
        api_key = self._get_api_key()
        
        if not api_key:
            logger.warning("No Google API key found. LLM features will be disabled.")
            return None
        
        try:
            # Set the API key for the session
            os.environ["GOOGLE_API_KEY"] = api_key
            chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
            logger.info("Gemini initialized successfully with API key")
            return chat
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None

    def _get_api_key(self) -> Optional[str]:
        """Get API key from database only - no environment variable fallback"""
        
        logger.info(f"Getting API key for user_id: {self.user_id}")
        
        # Only get from database if user_id is provided
        if self.user_id:
            try:
                # Get user's default Google API key
                logger.info(f"Looking up API key for user {self.user_id} and provider 'google'")
                api_key = auth_service.get_user_default_api_key(self.user_id, "google")
                logger.info(f"API key lookup result: {api_key[:10] + '...' if api_key else 'None'}")
                
                if api_key:
                    logger.info("Using API key from database")
                    return api_key
                else:
                    logger.warning("No API key found in database")
            except Exception as e:
                logger.warning(f"Failed to get API key from database: {e}")
                import traceback
                logger.warning(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning("No user_id provided to summarizer")
        
        logger.warning("No API key found in database - user must provide their own API key")
        return None



    def set_user_id(self, user_id: str):
        """Set user ID for API key lookup"""
        self.user_id = user_id
        # Reinitialize with new user context
        self.chat = self._initialize_gemini()

    def has_api_key(self) -> bool:
        """Check if API key is available"""
        return self._get_api_key() is not None

    def get_api_key_source(self) -> str:
        """Get the source of the current API key"""
        if self.user_id:
            try:
                api_key = auth_service.get_user_default_api_key(self.user_id, "google")
                if api_key:
                    return "database"
            except Exception:
                pass
        
        return "none"

    def _create_comprehensive_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content summarizer. Create a comprehensive summary that captures all key points, main arguments, and important details from the transcript. Focus on accuracy and completeness while maintaining readability."),
            ("human", "Please provide a comprehensive summary of this YouTube transcript:\n\n{text}")
        ])

    def _create_bullet_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content summarizer. Create a bullet-point summary that highlights the main points and key takeaways from the transcript. Use clear, concise bullet points."),
            ("human", "Please provide a bullet-point summary of this YouTube transcript:\n\n{text}")
        ])

    def _create_insights_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content analyst. Extract the most important insights, key learnings, and actionable takeaways from the transcript. Focus on what's most valuable for the audience."),
            ("human", "Please extract key insights and learnings from this YouTube transcript:\n\n{text}")
        ])

    def _create_timeline_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content organizer. Create a chronological timeline of events, topics, or points discussed in the transcript. Organize information in a logical flow."),
            ("human", "Please create a timeline summary of this YouTube transcript:\n\n{text}")
        ])

    def _create_qa_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content analyst. Create a Q&A format summary by identifying the main questions or topics addressed in the transcript and providing clear answers."),
            ("human", "Please create a Q&A summary of this YouTube transcript:\n\n{text}")
        ])

    def _create_brief_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an expert content summarizer. Create a brief, concise summary that captures the essence of the transcript in just a few sentences. Focus on the core message."),
            ("human", "Please provide a brief summary of this YouTube transcript:\n\n{text}")
        ])

    def _get_cache_key(self, text: str, style: str) -> str:
        """Generate a cache key based on text content and style"""
        content_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{content_hash}_{style}.json"

    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """Load summary from cache if it exists"""
        cache_file = self.cache_dir / cache_key
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded summary from cache: {cache_key}")
                    return data.get('summary')
            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_key}: {e}")
        return None

    def _save_to_cache(self, cache_key: str, summary: str, metadata: Dict[str, Any]):
        """Save summary to cache"""
        cache_file = self.cache_dir / cache_key
        logger.info(f"Attempting to save cache to: {cache_file.absolute()}")
        logger.info(f"Cache directory exists: {self.cache_dir.exists()}")
        logger.info(f"Cache directory is writable: {os.access(self.cache_dir, os.W_OK)}")
        try:
            data = {
                'summary': summary,
                'metadata': metadata,
                'created_at': metadata.get('timestamp', '')
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved summary to cache: {cache_key}")
            # Verify file was written
            logger.info(f"File written successfully. File exists: {cache_file.exists()}")
            logger.info(f"File size: {cache_file.stat().st_size if cache_file.exists() else 'N/A'}")
            
        except Exception as e:
            logger.error(f"Failed to save cache file {cache_key}: {e}")

    def summarize(self, text: str, style: str = "comprehensive") -> Optional[str]:
        """
        Summarize text using Gemini 2.5 Flash with caching
        
        Args:
            text: The transcript text to summarize
            style: Summary style - "comprehensive", "bullet", "insights", "timeline", "qa", "brief"
            
        Returns:
            Summary text or None if failed
        """
        if not text.strip():
            logger.warning("Empty text provided for summarization")
            return None

        # Check cache first
        cache_key = self._get_cache_key(text, style)
        cached_summary = self._load_from_cache(cache_key)
        if cached_summary:
            return cached_summary

        # Check if API key is available
        if not self.has_api_key():
            logger.error("No API key available. Cannot generate summary.")
            return None

        # Check if Gemini is initialized
        if not self.chat:
            logger.error("Gemini not initialized. Cannot generate summary.")
            return None

        # Validate style
        if style not in self.prompts:
            logger.warning(f"Invalid style '{style}', using 'comprehensive'")
            style = "comprehensive"

        

        try:
            logger.info(f"Generating new summary with style: {style}")
            
            # Create chain using modern pipe syntax
            chain = self.prompts[style] | self.chat
            
            # Generate summary
            response = chain.invoke({"text": text})
            
            if response and response.content.strip():
                # Save to cache
                metadata = {
                    'style': style,
                    'text_length': len(text),
                    'summary_length': len(response.content),
                    'timestamp': str(Path().cwd())
                }
                self._save_to_cache(cache_key, response.content, metadata)
                
                logger.info(f"Successfully generated summary ({len(response.content)} chars)")
                return response.content.strip()
            else:
                logger.error("Empty response from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            return None

    def get_available_styles(self) -> list:
        """Get list of available summary styles"""
        return list(self.prompts.keys())

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_cached_summaries': len(cache_files),
            'cache_size_bytes': total_size,
            'cache_size_mb': round(total_size / (1024 * 1024), 2),
            'available_styles': self.get_available_styles()
        }

