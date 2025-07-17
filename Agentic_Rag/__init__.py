"""
PokerPy Agentic RAG System
Retrieval-Augmented Generation for Enhanced Poker Knowledge

This package implements a comprehensive RAG system that enhances the PokerPy
agents with intelligent knowledge retrieval and contextual information processing.
"""

from .rag.knowledge_base import PokerKnowledgeBase, KnowledgeDocument
from .rag.vector_store import VectorStore, EmbeddingService
from .rag.retrieval_agent import RetrievalAgent, QueryProcessor
from .rag.rag_orchestrator import RAGOrchestrator
from .rag.knowledge_sources import (
    PokerStrategySource,
    HandHistorySource, 
    CommunityContentSource,
    LearningMaterialSource
)

__all__ = [
    'PokerKnowledgeBase',
    'KnowledgeDocument', 
    'VectorStore',
    'EmbeddingService',
    'RetrievalAgent',
    'QueryProcessor',
    'RAGOrchestrator',
    'PokerStrategySource',
    'HandHistorySource',
    'CommunityContentSource', 
    'LearningMaterialSource'
]

__version__ = "1.0.0"
