"""
PokerPy Agentic RAG System
Retrieval-Augmented Generation for Enhanced Poker Knowledge

This package implements a comprehensive RAG system that enhances the PokerPy
agents with intelligent knowledge retrieval and contextual information processing.
"""

from .knowledge_base import PokerKnowledgeBase, KnowledgeDocument
from .vector_store import VectorStore, EmbeddingService
from .retrieval_agent import RetrievalAgent, QueryProcessor
from .rag_orchestrator import RAGOrchestrator
from .knowledge_sources import (
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

