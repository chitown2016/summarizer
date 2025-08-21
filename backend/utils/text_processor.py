import re
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        self.chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better processing
        """
        try:
            # Clean the text
            cleaned_text = self._clean_text(text)
            
            # Split into sentences first
            sentences = self._split_into_sentences(cleaned_text)
            
            # Create chunks
            chunks = []
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                # If adding this sentence would exceed chunk size
                if current_length + sentence_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "word_count": len(chunk_text.split()),
                        "start_time": None,  # Could be extracted from transcript timestamps
                        "end_time": None
                    })
                    
                    # Start new chunk with overlap
                    overlap_sentences = self._get_overlap_sentences(current_chunk)
                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s) for s in current_chunk)
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # Add the last chunk if it exists
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "word_count": len(chunk_text.split()),
                    "start_time": None,
                    "end_time": None
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            # Fallback: simple chunking
            return self._simple_chunk_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        # Normalize quotes and apostrophes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be improved with NLTK
        sentences = re.split(r'[.!?]+', text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter out very short fragments
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap between chunks"""
        if len(sentences) <= 1:
            return []
        
        # Calculate how many sentences to include for overlap
        overlap_length = 0
        overlap_sentences = []
        
        for sentence in reversed(sentences):
            if overlap_length + len(sentence) <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_length += len(sentence)
            else:
                break
        
        return overlap_sentences
    
    def _simple_chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Fallback simple text chunking"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "text": chunk_text,
                "word_count": len(chunk_words),
                "start_time": None,
                "end_time": None
            })
        
        return chunks
    
    def extract_timestamps(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract timestamps from transcript text (if available)
        Format: [00:00:00] or (00:00:00) or similar
        """
        timestamp_pattern = r'\[?(\d{1,2}:\d{2}:\d{2})\]?'
        timestamps = []
        
        for match in re.finditer(timestamp_pattern, text):
            timestamp = match.group(1)
            position = match.start()
            timestamps.append({
                "timestamp": timestamp,
                "position": position,
                "text": match.group(0)
            })
        
        return timestamps
    
    def remove_timestamps(self, text: str) -> str:
        """Remove timestamp markers from text"""
        # Remove various timestamp formats
        text = re.sub(r'\[?\d{1,2}:\d{2}:\d{2}\]?', '', text)
        text = re.sub(r'\(\d{1,2}:\d{2}:\d{2}\)', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def get_word_count(self, text: str) -> int:
        """Get word count of text"""
        return len(text.split())
    
    def get_reading_time(self, text: str, words_per_minute: int = 200) -> float:
        """Estimate reading time in minutes"""
        word_count = self.get_word_count(text)
        return word_count / words_per_minute

