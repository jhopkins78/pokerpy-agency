"""
Vector Store and Embedding System for Poker Knowledge
Provides semantic search capabilities for RAG retrieval
"""

import numpy as np
import json
import pickle
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
import requests
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import sqlite3
import threading

from .knowledge_base import KnowledgeDocument

@dataclass
class EmbeddingVector:
    """Represents a document embedding vector"""
    document_id: str
    vector: np.ndarray
    metadata: Dict[str, Any]
    created_at: datetime
    model_name: str
    vector_dimension: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'document_id': self.document_id,
            'vector': self.vector.tolist(),
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'model_name': self.model_name,
            'vector_dimension': self.vector_dimension
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbeddingVector':
        """Create from dictionary"""
        return cls(
            document_id=data['document_id'],
            vector=np.array(data['vector']),
            metadata=data['metadata'],
            created_at=datetime.fromisoformat(data['created_at']),
            model_name=data['model_name'],
            vector_dimension=data['vector_dimension']
        )

class EmbeddingService:
    """
    Service for generating embeddings from text
    Supports multiple embedding models and caching
    """
    
    def __init__(self, model_name: str = "tfidf", cache_embeddings: bool = True):
        self.model_name = model_name
        self.cache_embeddings = cache_embeddings
        self.embedding_cache = {}
        self.logger = logging.getLogger("embedding_service")
        
        # Initialize embedding model
        if model_name == "tfidf":
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            self.is_fitted = False
        else:
            # For future integration with other embedding models
            self.vectorizer = None
            self.is_fitted = False
    
    def fit_vectorizer(self, documents: List[str]):
        """Fit the vectorizer on a corpus of documents"""
        if self.model_name == "tfidf":
            self.vectorizer.fit(documents)
            self.is_fitted = True
            self.logger.info(f"Fitted TF-IDF vectorizer on {len(documents)} documents")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text"""
        try:
            # Check cache first
            if self.cache_embeddings:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                if text_hash in self.embedding_cache:
                    return self.embedding_cache[text_hash]
            
            # Generate embedding based on model
            if self.model_name == "tfidf":
                if not self.is_fitted:
                    # Fit on single document if not fitted
                    self.vectorizer.fit([text])
                    self.is_fitted = True
                
                vector = self.vectorizer.transform([text]).toarray()[0]
                
                # Cache the result
                if self.cache_embeddings:
                    self.embedding_cache[text_hash] = vector
                
                return vector
            
            else:
                # Placeholder for other embedding models
                # Could integrate with OpenAI, Sentence Transformers, etc.
                raise NotImplementedError(f"Embedding model {self.model_name} not implemented")
        
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(100)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            if self.model_name == "tfidf":
                if not self.is_fitted:
                    self.vectorizer.fit(texts)
                    self.is_fitted = True
                
                vectors = self.vectorizer.transform(texts).toarray()
                return [vector for vector in vectors]
            
            else:
                # For other models, generate individually
                return [self.generate_embedding(text) for text in texts]
        
        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {e}")
            return [np.zeros(100) for _ in texts]
    
    def get_vector_dimension(self) -> int:
        """Get the dimension of embedding vectors"""
        if self.model_name == "tfidf" and self.is_fitted:
            return len(self.vectorizer.get_feature_names_out())
        return 100  # Default dimension

class VectorStore:
    """
    Vector database for storing and searching document embeddings
    Provides similarity search and retrieval capabilities
    """
    
    def __init__(self, storage_path: str = None, embedding_service: EmbeddingService = None):
        self.storage_path = storage_path or "/tmp/vector_store.db"
        self.embedding_service = embedding_service or EmbeddingService()
        self.vectors: Dict[str, EmbeddingVector] = {}
        self.logger = logging.getLogger("vector_store")
        self._lock = threading.Lock()
        
        # Initialize SQLite database for persistent storage
        self._init_database()
        
        # Load existing vectors
        self.load_vectors()
    
    def _init_database(self):
        """Initialize SQLite database for vector storage"""
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    document_id TEXT PRIMARY KEY,
                    vector BLOB,
                    metadata TEXT,
                    created_at TEXT,
                    model_name TEXT,
                    vector_dimension INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_model_name ON embeddings(model_name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON embeddings(created_at)
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Initialized vector database at {self.storage_path}")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    def add_document_embedding(self, document: KnowledgeDocument) -> bool:
        """Generate and store embedding for a document"""
        try:
            with self._lock:
                # Prepare text for embedding
                text_content = f"{document.title} {document.content}"
                
                # Generate embedding
                vector = self.embedding_service.generate_embedding(text_content)
                
                # Create embedding vector object
                embedding_vector = EmbeddingVector(
                    document_id=document.id,
                    vector=vector,
                    metadata={
                        'document_type': document.document_type.value,
                        'skill_level': document.skill_level.value,
                        'tags': document.tags,
                        'title': document.title,
                        'confidence_score': document.confidence_score
                    },
                    created_at=datetime.now(),
                    model_name=self.embedding_service.model_name,
                    vector_dimension=len(vector)
                )
                
                # Store in memory
                self.vectors[document.id] = embedding_vector
                
                # Store in database
                self._save_vector_to_db(embedding_vector)
                
                self.logger.info(f"Added embedding for document: {document.id}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error adding document embedding: {e}")
            return False
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5,
                      min_similarity: float = 0.1,
                      filters: Dict[str, Any] = None) -> List[Tuple[str, float]]:
        """Search for similar documents using vector similarity"""
        try:
            # Generate query embedding
            query_vector = self.embedding_service.generate_embedding(query)
            
            if len(self.vectors) == 0:
                return []
            
            # Calculate similarities
            similarities = []
            for doc_id, embedding_vector in self.vectors.items():
                # Apply filters if provided
                if filters and not self._matches_filters(embedding_vector, filters):
                    continue
                
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    query_vector.reshape(1, -1),
                    embedding_vector.vector.reshape(1, -1)
                )[0][0]
                
                if similarity >= min_similarity:
                    similarities.append((doc_id, similarity))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
        
        except Exception as e:
            self.logger.error(f"Error searching similar documents: {e}")
            return []
    
    def get_embedding(self, document_id: str) -> Optional[EmbeddingVector]:
        """Get embedding vector for a document"""
        return self.vectors.get(document_id)
    
    def remove_embedding(self, document_id: str) -> bool:
        """Remove embedding for a document"""
        try:
            with self._lock:
                if document_id in self.vectors:
                    del self.vectors[document_id]
                
                # Remove from database
                conn = sqlite3.connect(self.storage_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
                conn.commit()
                conn.close()
                
                self.logger.info(f"Removed embedding for document: {document_id}")
                return True
            
        except Exception as e:
            self.logger.error(f"Error removing embedding: {e}")
            return False
    
    def update_embedding(self, document: KnowledgeDocument) -> bool:
        """Update embedding for a document"""
        # Remove existing embedding and add new one
        self.remove_embedding(document.id)
        return self.add_document_embedding(document)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        stats = {
            'total_vectors': len(self.vectors),
            'model_name': self.embedding_service.model_name,
            'vector_dimension': self.embedding_service.get_vector_dimension() if self.vectors else 0,
            'by_document_type': {},
            'by_skill_level': {}
        }
        
        # Count by document type and skill level
        for embedding_vector in self.vectors.values():
            doc_type = embedding_vector.metadata.get('document_type', 'unknown')
            skill_level = embedding_vector.metadata.get('skill_level', 'unknown')
            
            stats['by_document_type'][doc_type] = stats['by_document_type'].get(doc_type, 0) + 1
            stats['by_skill_level'][skill_level] = stats['by_skill_level'].get(skill_level, 0) + 1
        
        return stats
    
    def rebuild_index(self, documents: List[KnowledgeDocument]) -> bool:
        """Rebuild the entire vector index"""
        try:
            self.logger.info("Rebuilding vector index...")
            
            # Clear existing vectors
            self.vectors.clear()
            
            # Clear database
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM embeddings")
            conn.commit()
            conn.close()
            
            # Prepare texts for batch embedding
            texts = [f"{doc.title} {doc.content}" for doc in documents]
            
            # Fit vectorizer on all documents
            if hasattr(self.embedding_service, 'fit_vectorizer'):
                self.embedding_service.fit_vectorizer(texts)
            
            # Generate embeddings for all documents
            vectors = self.embedding_service.generate_batch_embeddings(texts)
            
            # Store embeddings
            for document, vector in zip(documents, vectors):
                embedding_vector = EmbeddingVector(
                    document_id=document.id,
                    vector=vector,
                    metadata={
                        'document_type': document.document_type.value,
                        'skill_level': document.skill_level.value,
                        'tags': document.tags,
                        'title': document.title,
                        'confidence_score': document.confidence_score
                    },
                    created_at=datetime.now(),
                    model_name=self.embedding_service.model_name,
                    vector_dimension=len(vector)
                )
                
                self.vectors[document.id] = embedding_vector
                self._save_vector_to_db(embedding_vector)
            
            self.logger.info(f"Rebuilt vector index with {len(documents)} documents")
            return True
        
        except Exception as e:
            self.logger.error(f"Error rebuilding index: {e}")
            return False
    
    def load_vectors(self) -> bool:
        """Load vectors from database"""
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM embeddings")
            rows = cursor.fetchall()
            
            for row in rows:
                document_id, vector_blob, metadata_json, created_at, model_name, vector_dimension = row
                
                # Deserialize vector
                vector = pickle.loads(vector_blob)
                metadata = json.loads(metadata_json)
                
                embedding_vector = EmbeddingVector(
                    document_id=document_id,
                    vector=vector,
                    metadata=metadata,
                    created_at=datetime.fromisoformat(created_at),
                    model_name=model_name,
                    vector_dimension=vector_dimension
                )
                
                self.vectors[document_id] = embedding_vector
            
            conn.close()
            self.logger.info(f"Loaded {len(self.vectors)} vectors from database")
            return True
        
        except Exception as e:
            self.logger.error(f"Error loading vectors: {e}")
            return False
    
    def _save_vector_to_db(self, embedding_vector: EmbeddingVector):
        """Save embedding vector to database"""
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            
            # Serialize vector and metadata
            vector_blob = pickle.dumps(embedding_vector.vector)
            metadata_json = json.dumps(embedding_vector.metadata)
            
            cursor.execute('''
                INSERT OR REPLACE INTO embeddings 
                (document_id, vector, metadata, created_at, model_name, vector_dimension)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                embedding_vector.document_id,
                vector_blob,
                metadata_json,
                embedding_vector.created_at.isoformat(),
                embedding_vector.model_name,
                embedding_vector.vector_dimension
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            self.logger.error(f"Error saving vector to database: {e}")
    
    def _matches_filters(self, embedding_vector: EmbeddingVector, filters: Dict[str, Any]) -> bool:
        """Check if embedding vector matches the provided filters"""
        for key, value in filters.items():
            if key in embedding_vector.metadata:
                if isinstance(value, list):
                    if embedding_vector.metadata[key] not in value:
                        return False
                else:
                    if embedding_vector.metadata[key] != value:
                        return False
        return True

