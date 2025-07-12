import os
import json
import pickle
import numpy as np
from typing import List, Dict, Optional, Any
import openai
from dataclasses import dataclass
import logging
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeChunk:
    id: str
    content: str
    metadata: Dict
    embedding: Optional[np.ndarray] = None
    category: str = "general"
    source: str = ""
    relevance_score: float = 0.0

class RAGSystem:
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.client = openai.OpenAI()
        self.embeddings_cache = {}
        self.knowledge_chunks = []
        self.categories = {
            "poker_strategy": "Core poker strategy and tactics",
            "psychology": "Mental game and psychological aspects",
            "probability": "Mathematical concepts and odds",
            "game_theory": "Game theory applications in poker",
            "personal_development": "Self-improvement and life skills",
            "bankroll_management": "Financial aspects of poker",
            "tournament_strategy": "Tournament-specific strategies",
            "cash_game_strategy": "Cash game specific strategies"
        }
        
        # Initialize the system
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base from files"""
        try:
            # Create knowledge base directory if it doesn't exist
            self.knowledge_base_path.mkdir(exist_ok=True)
            
            # Load existing embeddings cache
            cache_file = self.knowledge_base_path / "embeddings_cache.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
            
            # Load knowledge chunks
            chunks_file = self.knowledge_base_path / "knowledge_chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    chunks_data = json.load(f)
                    self.knowledge_chunks = [
                        KnowledgeChunk(**chunk) for chunk in chunks_data
                    ]
            else:
                # Create initial knowledge base
                self._create_initial_knowledge_base()
                
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {str(e)}")
            self._create_initial_knowledge_base()
    
    def _create_initial_knowledge_base(self):
        """Create initial knowledge base with core poker concepts"""
        initial_knowledge = [
            {
                "content": "Position is one of the most important concepts in poker. Playing in position means acting after your opponents, giving you more information to make better decisions. Late position (button and cutoff) allows for wider opening ranges and more profitable bluffs.",
                "category": "poker_strategy",
                "source": "core_concepts",
                "metadata": {"topic": "position", "difficulty": "beginner"}
            },
            {
                "content": "Bankroll management is crucial for long-term success. A general rule is to have at least 20-30 buy-ins for cash games and 100+ buy-ins for tournaments. Never play with money you can't afford to lose.",
                "category": "bankroll_management",
                "source": "core_concepts",
                "metadata": {"topic": "bankroll", "difficulty": "beginner"}
            },
            {
                "content": "Tilt is the enemy of good poker. When emotions take over, decision-making suffers. Recognize tilt early through physical and mental signs: increased heart rate, frustration, deviation from optimal strategy. Take breaks when needed.",
                "category": "psychology",
                "source": "mental_game",
                "metadata": {"topic": "tilt_control", "difficulty": "intermediate"}
            },
            {
                "content": "Pot odds are the ratio of the current pot size to the cost of a call. If the pot is $100 and you need to call $20, you're getting 5:1 pot odds. Compare this to your hand's equity to make profitable decisions.",
                "category": "probability",
                "source": "mathematics",
                "metadata": {"topic": "pot_odds", "difficulty": "intermediate"}
            },
            {
                "content": "Game theory optimal (GTO) play involves making decisions that are unexploitable by opponents. While perfect GTO is impossible for humans, understanding GTO concepts helps create a solid baseline strategy.",
                "category": "game_theory",
                "source": "advanced_concepts",
                "metadata": {"topic": "gto", "difficulty": "advanced"}
            },
            {
                "content": "Discipline in poker mirrors discipline in life. The ability to fold strong hands when beaten, stick to bankroll management, and maintain emotional control translates to better decision-making in all areas of life.",
                "category": "personal_development",
                "source": "life_lessons",
                "metadata": {"topic": "discipline", "difficulty": "beginner"}
            },
            {
                "content": "Tournament strategy differs significantly from cash games. ICM (Independent Chip Model) considerations become crucial near the bubble and final table. Survival often trumps chip accumulation in key spots.",
                "category": "tournament_strategy",
                "source": "tournament_guide",
                "metadata": {"topic": "icm", "difficulty": "advanced"}
            },
            {
                "content": "Reading opponents involves observing betting patterns, physical tells, and timing tells. Look for deviations from baseline behavior. Online, focus on bet sizing patterns and timing.",
                "category": "psychology",
                "source": "opponent_reading",
                "metadata": {"topic": "tells", "difficulty": "intermediate"}
            }
        ]
        
        for item in initial_knowledge:
            chunk = KnowledgeChunk(
                id=self._generate_chunk_id(item["content"]),
                content=item["content"],
                category=item["category"],
                source=item["source"],
                metadata=item["metadata"]
            )
            self.knowledge_chunks.append(chunk)
        
        # Generate embeddings for initial knowledge
        self._generate_embeddings()
        self._save_knowledge_base()
    
    def _generate_chunk_id(self, content: str) -> str:
        """Generate a unique ID for a knowledge chunk"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_embeddings(self):
        """Generate embeddings for all knowledge chunks"""
        try:
            for chunk in self.knowledge_chunks:
                if chunk.id not in self.embeddings_cache:
                    # Generate embedding using OpenAI
                    response = self.client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=chunk.content
                    )
                    embedding = np.array(response.data[0].embedding)
                    self.embeddings_cache[chunk.id] = embedding
                    chunk.embedding = embedding
                else:
                    chunk.embedding = self.embeddings_cache[chunk.id]
                    
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
    
    def _save_knowledge_base(self):
        """Save knowledge base to files"""
        try:
            # Save embeddings cache
            cache_file = self.knowledge_base_path / "embeddings_cache.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            
            # Save knowledge chunks (without embeddings to avoid JSON issues)
            chunks_data = []
            for chunk in self.knowledge_chunks:
                chunk_dict = {
                    "id": chunk.id,
                    "content": chunk.content,
                    "category": chunk.category,
                    "source": chunk.source,
                    "metadata": chunk.metadata
                }
                chunks_data.append(chunk_dict)
            
            chunks_file = self.knowledge_base_path / "knowledge_chunks.json"
            with open(chunks_file, 'w') as f:
                json.dump(chunks_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving knowledge base: {str(e)}")
    
    def search(self, query: str, category: str = "all", limit: int = 5) -> List[Dict]:
        """Search the knowledge base for relevant information"""
        try:
            if not self.knowledge_chunks:
                return []
            
            # Generate query embedding
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = np.array(response.data[0].embedding)
            
            # Calculate similarities
            results = []
            for chunk in self.knowledge_chunks:
                if category != "all" and chunk.category != category:
                    continue
                
                if chunk.embedding is not None:
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, chunk.embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk.embedding)
                    )
                    
                    results.append({
                        "id": chunk.id,
                        "content": chunk.content,
                        "category": chunk.category,
                        "source": chunk.source,
                        "metadata": chunk.metadata,
                        "relevance_score": float(similarity)
                    })
            
            # Sort by relevance and return top results
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def add_knowledge(self, content: str, category: str, source: str, metadata: Dict = None) -> str:
        """Add new knowledge to the base"""
        try:
            if metadata is None:
                metadata = {}
            
            chunk = KnowledgeChunk(
                id=self._generate_chunk_id(content),
                content=content,
                category=category,
                source=source,
                metadata=metadata
            )
            
            # Generate embedding
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=content
            )
            embedding = np.array(response.data[0].embedding)
            chunk.embedding = embedding
            self.embeddings_cache[chunk.id] = embedding
            
            # Add to knowledge base
            self.knowledge_chunks.append(chunk)
            self._save_knowledge_base()
            
            return chunk.id
            
        except Exception as e:
            logger.error(f"Error adding knowledge: {str(e)}")
            return ""
    
    def get_categories(self) -> Dict[str, str]:
        """Get available knowledge categories"""
        return self.categories
    
    def get_knowledge_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        stats = {
            "total_chunks": len(self.knowledge_chunks),
            "categories": {},
            "sources": {}
        }
        
        for chunk in self.knowledge_chunks:
            # Count by category
            if chunk.category in stats["categories"]:
                stats["categories"][chunk.category] += 1
            else:
                stats["categories"][chunk.category] = 1
            
            # Count by source
            if chunk.source in stats["sources"]:
                stats["sources"][chunk.source] += 1
            else:
                stats["sources"][chunk.source] = 1
        
        return stats
    
    def update_knowledge(self, chunk_id: str, content: str = None, metadata: Dict = None) -> bool:
        """Update existing knowledge chunk"""
        try:
            for i, chunk in enumerate(self.knowledge_chunks):
                if chunk.id == chunk_id:
                    if content:
                        chunk.content = content
                        # Regenerate embedding
                        response = self.client.embeddings.create(
                            model="text-embedding-ada-002",
                            input=content
                        )
                        embedding = np.array(response.data[0].embedding)
                        chunk.embedding = embedding
                        self.embeddings_cache[chunk.id] = embedding
                    
                    if metadata:
                        chunk.metadata.update(metadata)
                    
                    self._save_knowledge_base()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating knowledge: {str(e)}")
            return False
    
    def delete_knowledge(self, chunk_id: str) -> bool:
        """Delete knowledge chunk"""
        try:
            for i, chunk in enumerate(self.knowledge_chunks):
                if chunk.id == chunk_id:
                    del self.knowledge_chunks[i]
                    if chunk_id in self.embeddings_cache:
                        del self.embeddings_cache[chunk_id]
                    self._save_knowledge_base()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting knowledge: {str(e)}")
            return False

