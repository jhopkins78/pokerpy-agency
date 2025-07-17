"""
Poker Knowledge Base System
Manages structured poker knowledge for RAG retrieval
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import logging

class DocumentType(Enum):
    """Types of poker knowledge documents"""
    STRATEGY = "strategy"
    HAND_ANALYSIS = "hand_analysis"
    CONCEPT = "concept"
    RULE = "rule"
    TUTORIAL = "tutorial"
    FAQ = "faq"
    COMMUNITY_POST = "community_post"
    LEARNING_MODULE = "learning_module"
    HISTORICAL_HAND = "historical_hand"
    PLAYER_PROFILE = "player_profile"

class SkillLevel(Enum):
    """Skill levels for content targeting"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    ALL_LEVELS = "all_levels"

@dataclass
class KnowledgeDocument:
    """Represents a single piece of poker knowledge"""
    id: str
    title: str
    content: str
    document_type: DocumentType
    skill_level: SkillLevel
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    source: Optional[str] = None
    author: Optional[str] = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        """Validate and process document after initialization"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.document_type, str):
            self.document_type = DocumentType(self.document_type)
        
        if isinstance(self.skill_level, str):
            self.skill_level = SkillLevel(self.skill_level)
        
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        data = asdict(self)
        data['document_type'] = self.document_type.value
        data['skill_level'] = self.skill_level.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeDocument':
        """Create document from dictionary"""
        return cls(**data)
    
    def get_content_hash(self) -> str:
        """Generate hash of document content for deduplication"""
        content_str = f"{self.title}|{self.content}|{self.document_type.value}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def update_content(self, new_content: str, new_title: str = None):
        """Update document content and increment version"""
        self.content = new_content
        if new_title:
            self.title = new_title
        self.updated_at = datetime.now()
        self.version += 1

class PokerKnowledgeBase:
    """
    Comprehensive poker knowledge management system
    Stores, indexes, and retrieves poker knowledge documents
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/tmp/poker_knowledge.json"
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.indexes = {
            'by_type': {},
            'by_skill_level': {},
            'by_tags': {},
            'by_content_hash': {}
        }
        self.logger = logging.getLogger("knowledge_base")
        
        # Load existing knowledge if available
        self.load_knowledge()
        
        # Initialize with core poker knowledge
        if not self.documents:
            self._initialize_core_knowledge()
    
    def add_document(self, document: KnowledgeDocument) -> bool:
        """Add a new document to the knowledge base"""
        try:
            # Check for duplicates
            content_hash = document.get_content_hash()
            if content_hash in self.indexes['by_content_hash']:
                existing_id = self.indexes['by_content_hash'][content_hash]
                self.logger.warning(f"Duplicate content detected. Existing document: {existing_id}")
                return False
            
            # Add document
            self.documents[document.id] = document
            
            # Update indexes
            self._update_indexes(document)
            
            self.logger.info(f"Added document: {document.id} - {document.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding document: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve a document by ID"""
        return self.documents.get(document_id)
    
    def search_documents(self, 
                        query: str = None,
                        document_type: DocumentType = None,
                        skill_level: SkillLevel = None,
                        tags: List[str] = None,
                        limit: int = 10) -> List[KnowledgeDocument]:
        """Search documents with various filters"""
        results = list(self.documents.values())
        
        # Filter by document type
        if document_type:
            results = [doc for doc in results if doc.document_type == document_type]
        
        # Filter by skill level
        if skill_level:
            results = [doc for doc in results 
                      if doc.skill_level == skill_level or doc.skill_level == SkillLevel.ALL_LEVELS]
        
        # Filter by tags
        if tags:
            results = [doc for doc in results 
                      if any(tag in doc.tags for tag in tags)]
        
        # Text search in title and content
        if query:
            query_lower = query.lower()
            results = [doc for doc in results 
                      if query_lower in doc.title.lower() or query_lower in doc.content.lower()]
        
        # Sort by relevance (confidence score and recency)
        results.sort(key=lambda x: (x.confidence_score, x.updated_at), reverse=True)
        
        return results[:limit]
    
    def get_documents_by_type(self, document_type: DocumentType) -> List[KnowledgeDocument]:
        """Get all documents of a specific type"""
        return [doc for doc in self.documents.values() if doc.document_type == document_type]
    
    def get_documents_by_skill_level(self, skill_level: SkillLevel) -> List[KnowledgeDocument]:
        """Get all documents for a specific skill level"""
        return [doc for doc in self.documents.values() 
                if doc.skill_level == skill_level or doc.skill_level == SkillLevel.ALL_LEVELS]
    
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing document"""
        try:
            if document_id not in self.documents:
                return False
            
            document = self.documents[document_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            document.updated_at = datetime.now()
            document.version += 1
            
            # Update indexes
            self._update_indexes(document)
            
            self.logger.info(f"Updated document: {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating document {document_id}: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the knowledge base"""
        try:
            if document_id not in self.documents:
                return False
            
            document = self.documents[document_id]
            
            # Remove from indexes
            self._remove_from_indexes(document)
            
            # Remove document
            del self.documents[document_id]
            
            self.logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = {
            'total_documents': len(self.documents),
            'by_type': {},
            'by_skill_level': {},
            'total_tags': len(self.indexes['by_tags']),
            'last_updated': max([doc.updated_at for doc in self.documents.values()]) if self.documents else None
        }
        
        # Count by type
        for doc_type in DocumentType:
            count = len([doc for doc in self.documents.values() if doc.document_type == doc_type])
            stats['by_type'][doc_type.value] = count
        
        # Count by skill level
        for skill_level in SkillLevel:
            count = len([doc for doc in self.documents.values() if doc.skill_level == skill_level])
            stats['by_skill_level'][skill_level.value] = count
        
        return stats
    
    def save_knowledge(self) -> bool:
        """Save knowledge base to storage"""
        try:
            data = {
                'documents': {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()},
                'metadata': {
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'document_count': len(self.documents)
                }
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved knowledge base to {self.storage_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving knowledge base: {e}")
            return False
    
    def load_knowledge(self) -> bool:
        """Load knowledge base from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load documents
            for doc_id, doc_data in data.get('documents', {}).items():
                document = KnowledgeDocument.from_dict(doc_data)
                self.documents[doc_id] = document
                self._update_indexes(document)
            
            self.logger.info(f"Loaded {len(self.documents)} documents from {self.storage_path}")
            return True
            
        except FileNotFoundError:
            self.logger.info("No existing knowledge base found, starting fresh")
            return True
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            return False
    
    def _update_indexes(self, document: KnowledgeDocument):
        """Update all indexes for a document"""
        # Index by type
        doc_type = document.document_type.value
        if doc_type not in self.indexes['by_type']:
            self.indexes['by_type'][doc_type] = []
        if document.id not in self.indexes['by_type'][doc_type]:
            self.indexes['by_type'][doc_type].append(document.id)
        
        # Index by skill level
        skill_level = document.skill_level.value
        if skill_level not in self.indexes['by_skill_level']:
            self.indexes['by_skill_level'][skill_level] = []
        if document.id not in self.indexes['by_skill_level'][skill_level]:
            self.indexes['by_skill_level'][skill_level].append(document.id)
        
        # Index by tags
        for tag in document.tags:
            if tag not in self.indexes['by_tags']:
                self.indexes['by_tags'][tag] = []
            if document.id not in self.indexes['by_tags'][tag]:
                self.indexes['by_tags'][tag].append(document.id)
        
        # Index by content hash
        content_hash = document.get_content_hash()
        self.indexes['by_content_hash'][content_hash] = document.id
    
    def _remove_from_indexes(self, document: KnowledgeDocument):
        """Remove document from all indexes"""
        # Remove from type index
        doc_type = document.document_type.value
        if doc_type in self.indexes['by_type']:
            if document.id in self.indexes['by_type'][doc_type]:
                self.indexes['by_type'][doc_type].remove(document.id)
        
        # Remove from skill level index
        skill_level = document.skill_level.value
        if skill_level in self.indexes['by_skill_level']:
            if document.id in self.indexes['by_skill_level'][skill_level]:
                self.indexes['by_skill_level'][skill_level].remove(document.id)
        
        # Remove from tag indexes
        for tag in document.tags:
            if tag in self.indexes['by_tags']:
                if document.id in self.indexes['by_tags'][tag]:
                    self.indexes['by_tags'][tag].remove(document.id)
        
        # Remove from content hash index
        content_hash = document.get_content_hash()
        if content_hash in self.indexes['by_content_hash']:
            del self.indexes['by_content_hash'][content_hash]
    
    def _initialize_core_knowledge(self):
        """Initialize the knowledge base with core poker knowledge"""
        core_documents = [
            KnowledgeDocument(
                id="core_001",
                title="Texas Hold'em Basic Rules",
                content="""Texas Hold'em is the most popular form of poker. Each player receives two private cards (hole cards) and shares five community cards. Players make the best five-card hand using any combination of their hole cards and the community cards. The game consists of four betting rounds: preflop, flop, turn, and river.""",
                document_type=DocumentType.RULE,
                skill_level=SkillLevel.BEGINNER,
                tags=["texas-holdem", "rules", "basics"],
                metadata={"importance": "high", "category": "fundamentals"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source="core_knowledge",
                confidence_score=1.0
            ),
            KnowledgeDocument(
                id="core_002", 
                title="Pot Odds and Equity",
                content="""Pot odds are the ratio of the current pot size to the cost of a call. Equity is your percentage chance of winning the hand. To make profitable calls, your equity must be greater than the pot odds. For example, if the pot is $100 and you need to call $25, you need 20% equity to break even (25/(100+25) = 0.2).""",
                document_type=DocumentType.CONCEPT,
                skill_level=SkillLevel.INTERMEDIATE,
                tags=["pot-odds", "equity", "mathematics", "decision-making"],
                metadata={"importance": "high", "category": "mathematics"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source="core_knowledge",
                confidence_score=1.0
            ),
            KnowledgeDocument(
                id="core_003",
                title="Position in Poker",
                content="""Position refers to where you sit relative to the dealer button. Late position (button and cutoff) is advantageous because you act last and have more information. Early position (under the gun) is disadvantageous because you act first. Position is one of the most important factors in poker strategy.""",
                document_type=DocumentType.STRATEGY,
                skill_level=SkillLevel.BEGINNER,
                tags=["position", "strategy", "fundamentals"],
                metadata={"importance": "high", "category": "strategy"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source="core_knowledge",
                confidence_score=1.0
            ),
            KnowledgeDocument(
                id="core_004",
                title="Bankroll Management",
                content="""Bankroll management is crucial for long-term poker success. A general rule is to have at least 20-25 buy-ins for cash games and 50-100 buy-ins for tournaments. Never play with money you can't afford to lose. Move down in stakes if your bankroll drops below the recommended levels.""",
                document_type=DocumentType.STRATEGY,
                skill_level=SkillLevel.ALL_LEVELS,
                tags=["bankroll", "management", "psychology", "fundamentals"],
                metadata={"importance": "critical", "category": "psychology"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source="core_knowledge",
                confidence_score=1.0
            ),
            KnowledgeDocument(
                id="core_005",
                title="Reading Opponents and Tells",
                content="""Reading opponents involves observing betting patterns, timing tells, and physical tells. Online, focus on betting patterns and timing. Live poker includes physical tells like posture changes, breathing patterns, and hand movements. However, be careful not to overvalue tells - betting patterns are usually more reliable.""",
                document_type=DocumentType.STRATEGY,
                skill_level=SkillLevel.ADVANCED,
                tags=["reads", "tells", "psychology", "live-poker", "online-poker"],
                metadata={"importance": "medium", "category": "psychology"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source="core_knowledge",
                confidence_score=0.8
            )
        ]
        
        for document in core_documents:
            self.add_document(document)
        
        self.logger.info(f"Initialized knowledge base with {len(core_documents)} core documents")

