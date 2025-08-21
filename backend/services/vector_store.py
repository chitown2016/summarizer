import os
import json
import chromadb
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Initialize sentence transformer model
        self.embedding_model = SentenceTransformer(self.embedding_model)
        
        # Cache for collections
        self.collections = {}
    
    def _get_collection(self, video_id: str):
        """Get or create a collection for a video"""
        if video_id not in self.collections:
            try:
                self.collections[video_id] = self.client.get_collection(name=video_id)
            except:
                self.collections[video_id] = self.client.create_collection(
                    name=video_id,
                    metadata={"video_id": video_id}
                )
        return self.collections[video_id]
    
    def add_documents(self, video_id: str, chunks: List[Dict[str, Any]]):
        """Add document chunks to the vector store"""
        try:
            collection = self._get_collection(video_id)
            
            # Prepare documents for insertion
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk["text"])
                metadatas.append({
                    "video_id": video_id,
                    "chunk_index": i,
                    "start_time": chunk.get("start_time"),
                    "end_time": chunk.get("end_time"),
                    "word_count": len(chunk["text"].split())
                })
                ids.append(f"{video_id}_chunk_{i}")
            
            # Create embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store for video {video_id}")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(self, video_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in a video collection"""
        try:
            collection = self._get_collection(video_id)
            
            # Create query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search in collection
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "id": results["ids"][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def get_all_documents(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all documents from a video collection"""
        try:
            collection = self._get_collection(video_id)
            
            # Get all documents
            results = collection.get()
            
            # Format results
            documents = []
            if results["documents"]:
                for i in range(len(results["documents"])):
                    documents.append({
                        "text": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "id": results["ids"][i]
                    })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents from vector store: {e}")
            return []
    
    def delete_collection(self, video_id: str) -> bool:
        """Delete a video collection"""
        try:
            if video_id in self.collections:
                del self.collections[video_id]
            
            self.client.delete_collection(name=video_id)
            logger.info(f"Deleted collection for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def collection_exists(self, video_id: str) -> bool:
        """Check if a collection exists"""
        try:
            self.client.get_collection(name=video_id)
            return True
        except:
            return False
    
    def get_collection_count(self, video_id: str) -> int:
        """Get the number of documents in a collection"""
        try:
            collection = self._get_collection(video_id)
            return collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0

