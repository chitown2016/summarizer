import os
import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)

class Summarizer:
    def __init__(self):
        self.cache_dir = Path("data/summaries")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        load_dotenv(find_dotenv())
        
        # Initialize Gemini
        self.chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        
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
        try:
            data = {
                'summary': summary,
                'metadata': metadata,
                'created_at': metadata.get('timestamp', '')
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved summary to cache: {cache_key}")
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

        # Validate style
        if style not in self.prompts:
            logger.warning(f"Invalid style '{style}', using 'comprehensive'")
            style = "comprehensive"

        # Check cache first
        cache_key = self._get_cache_key(text, style)
        cached_summary = self._load_from_cache(cache_key)
        if cached_summary:
            return cached_summary

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

