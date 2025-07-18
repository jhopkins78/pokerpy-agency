"""
RAG Orchestrator for PokerPy
Integrates RAG capabilities with the existing agent system
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent, AgentMessage
from src.models.orchestrator import AgentOrchestrator
from src.models.poker_models import SkillLevel
from .knowledge_base import DocumentType, PokerKnowledgeBase, KnowledgeDocument
from .vector_store import VectorStore, EmbeddingService
from .retrieval_agent import RetrievalAgent, ProcessedQuery, RetrievalResult

@dataclass
class RAGEnhancedResponse:
    """Response enhanced with RAG-retrieved knowledge"""
    original_response: str
    retrieved_knowledge: List[KnowledgeDocument]
    enhanced_response: str
    confidence_score: float
    sources: List[str]
    metadata: Dict[str, Any]

class RAGOrchestrator:
    """
    Orchestrates RAG functionality across the PokerPy agent system
    Enhances existing agents with knowledge retrieval capabilities
    """
    
    def __init__(self, 
                 agent_orchestrator: AgentOrchestrator,
                 knowledge_base: PokerKnowledgeBase = None,
                 vector_store: VectorStore = None):
        self.agent_orchestrator = agent_orchestrator
        self.knowledge_base = knowledge_base or PokerKnowledgeBase()
        self.vector_store = vector_store or VectorStore()
        self.retrieval_agent = RetrievalAgent(self.knowledge_base, self.vector_store)
        self.logger = logging.getLogger("rag_orchestrator")
        
        # Register retrieval agent with main orchestrator
        self.agent_orchestrator.register_agent(self.retrieval_agent)
        
        # RAG configuration
        self.rag_config = {
            'enable_rag_enhancement': True,
            'max_retrieved_docs': 3,
            'min_similarity_threshold': 0.2,
            'enhance_all_responses': False,  # Only enhance when explicitly requested
            'cache_enhanced_responses': True
        }
        
        # Performance tracking
        self.rag_stats = {
            'total_rag_requests': 0,
            'successful_enhancements': 0,
            'average_enhancement_time': 0.0,
            'knowledge_base_hits': 0
        }
        
        # Response cache
        self.response_cache = {}
        self.cache_size_limit = 50
        
        # Define RAG-enhanced workflows
        self._define_rag_workflows()
    
    def _define_rag_workflows(self):
        """Define workflows that incorporate RAG functionality"""
        # Enhanced hand analysis workflow
        self.agent_orchestrator.define_workflow("rag_enhanced_hand_analysis", [
            "retrieval_agent", "hand_analyzer", "coach"
        ])
        
        # Enhanced coaching workflow
        self.agent_orchestrator.define_workflow("rag_enhanced_coaching", [
            "retrieval_agent", "coach"
        ])
        
        # Learning path with knowledge retrieval
        self.agent_orchestrator.define_workflow("rag_enhanced_learning", [
            "retrieval_agent", "learning_path"
        ])
        
        # Community post with fact-checking
        self.agent_orchestrator.define_workflow("rag_enhanced_community", [
            "retrieval_agent", "community"
        ])
    
    async def enhance_agent_response(self, 
                                   agent_id: str,
                                   original_query: str,
                                   agent_response: str,
                                   context: Dict[str, Any] = None) -> RAGEnhancedResponse:
        """Enhance an agent's response with RAG-retrieved knowledge"""
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = f"{agent_id}_{hash(original_query)}_{hash(agent_response)}"
            if cache_key in self.response_cache:
                return self.response_cache[cache_key]
            
            # Retrieve relevant knowledge
            retrieval_message = AgentMessage(
                id=f"rag_enhance_{datetime.now().timestamp()}",
                sender="rag_orchestrator",
                recipient="retrieval_agent",
                message_type="retrieve_knowledge",
                content={
                    'query': original_query,
                    'context': context or {},
                    'max_results': self.rag_config['max_retrieved_docs'],
                    'min_similarity': self.rag_config['min_similarity_threshold']
                },
                timestamp=datetime.now(),
                requires_response=True
            )
            
            # Get retrieval response
            retrieval_response = await self.retrieval_agent.process_message(retrieval_message)
            
            if not retrieval_response or not retrieval_response.content.get('success'):
                # Return original response if retrieval fails
                return RAGEnhancedResponse(
                    original_response=agent_response,
                    retrieved_knowledge=[],
                    enhanced_response=agent_response,
                    confidence_score=0.5,
                    sources=[],
                    metadata={'enhancement_failed': True}
                )
            
            # Extract retrieved documents
            retrieval_result = retrieval_response.content['retrieval_result']
            retrieved_docs = [
                KnowledgeDocument.from_dict(doc_data) 
                for doc_data in retrieval_result['documents']
            ]
            
            # Enhance response with retrieved knowledge
            enhanced_response = await self._enhance_response_with_knowledge(
                original_query, agent_response, retrieved_docs, context
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_enhancement_confidence(
                retrieved_docs, retrieval_result['similarity_scores']
            )
            
            # Extract sources
            sources = [doc.source or f"Knowledge Base - {doc.title}" for doc in retrieved_docs]
            
            # Create enhanced response
            rag_enhanced = RAGEnhancedResponse(
                original_response=agent_response,
                retrieved_knowledge=retrieved_docs,
                enhanced_response=enhanced_response,
                confidence_score=confidence_score,
                sources=sources,
                metadata={
                    'retrieval_time': retrieval_result['retrieval_time'],
                    'total_retrieved': len(retrieved_docs),
                    'enhancement_time': (datetime.now() - start_time).total_seconds(),
                    'agent_id': agent_id
                }
            )
            
            # Update stats
            self.rag_stats['total_rag_requests'] += 1
            self.rag_stats['successful_enhancements'] += 1
            enhancement_time = (datetime.now() - start_time).total_seconds()
            self.rag_stats['average_enhancement_time'] = (
                (self.rag_stats['average_enhancement_time'] * (self.rag_stats['total_rag_requests'] - 1) + enhancement_time)
                / self.rag_stats['total_rag_requests']
            )
            
            # Cache result
            if len(self.response_cache) < self.cache_size_limit:
                self.response_cache[cache_key] = rag_enhanced
            
            return rag_enhanced
        
        except Exception as e:
            self.logger.error(f"Error enhancing response: {e}")
            self.rag_stats['total_rag_requests'] += 1
            
            # Return original response on error
            return RAGEnhancedResponse(
                original_response=agent_response,
                retrieved_knowledge=[],
                enhanced_response=agent_response,
                confidence_score=0.5,
                sources=[],
                metadata={'enhancement_error': str(e)}
            )
    
    async def _enhance_response_with_knowledge(self,
                                             query: str,
                                             original_response: str,
                                             retrieved_docs: List[KnowledgeDocument],
                                             context: Dict[str, Any] = None) -> str:
        """Enhance response by incorporating retrieved knowledge"""
        if not retrieved_docs:
            return original_response
        
        try:
            # Extract relevant information from retrieved documents
            relevant_info = []
            for doc in retrieved_docs:
                if doc.confidence_score > 0.7:  # Only use high-confidence documents
                    relevant_info.append({
                        'title': doc.title,
                        'content': doc.content,
                        'type': doc.document_type.value,
                        'skill_level': doc.skill_level.value
                    })
            
            if not relevant_info:
                return original_response
            
            # Create enhanced response
            enhanced_parts = [original_response]
            
            # Add relevant knowledge
            if len(relevant_info) > 0:
                enhanced_parts.append("\n\n**Additional Information:**")
                
                for info in relevant_info[:2]:  # Limit to top 2 most relevant
                    if info['type'] == 'concept':
                        enhanced_parts.append(f"\n• **{info['title']}**: {info['content'][:200]}...")
                    elif info['type'] == 'strategy':
                        enhanced_parts.append(f"\n• **Strategy Note**: {info['content'][:150]}...")
                    elif info['type'] == 'rule':
                        enhanced_parts.append(f"\n• **Rule Reference**: {info['content'][:150]}...")
            
            # Add sources note
            if len(retrieved_docs) > 0:
                enhanced_parts.append(f"\n\n*This response was enhanced with information from {len(retrieved_docs)} knowledge sources.*")
            
            return "".join(enhanced_parts)
        
        except Exception as e:
            self.logger.error(f"Error in response enhancement: {e}")
            return original_response
    
    def _calculate_enhancement_confidence(self, 
                                        retrieved_docs: List[KnowledgeDocument],
                                        similarity_scores: List[float]) -> float:
        """Calculate confidence score for the enhancement"""
        if not retrieved_docs or not similarity_scores:
            return 0.5
        
        # Base confidence on similarity scores and document confidence
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        avg_doc_confidence = sum(doc.confidence_score for doc in retrieved_docs) / len(retrieved_docs)
        
        # Combine scores
        confidence = (avg_similarity * 0.6) + (avg_doc_confidence * 0.4)
        
        # Boost confidence if we have multiple high-quality sources
        if len(retrieved_docs) >= 2 and avg_similarity > 0.5:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def execute_rag_workflow(self, 
                                 workflow_name: str,
                                 initial_data: Dict[str, Any],
                                 user_id: str = None) -> Dict[str, Any]:
        """Execute a RAG-enhanced workflow"""
        try:
            # Add RAG context to initial data
            initial_data['rag_enabled'] = True
            initial_data['rag_config'] = self.rag_config
            
            # Execute the workflow through the main orchestrator
            result = await self.agent_orchestrator.execute_workflow(
                workflow_name, initial_data, user_id
            )
            
            # Post-process results to include RAG metadata
            if 'results' in result:
                result['rag_metadata'] = {
                    'workflow_enhanced': True,
                    'knowledge_sources_used': len(self.knowledge_base.documents),
                    'vector_store_size': len(self.vector_store.vectors)
                }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error executing RAG workflow: {e}")
            raise e
    
    async def add_knowledge_from_interaction(self,
                                           user_query: str,
                                           agent_response: str,
                                           user_feedback: Dict[str, Any] = None):
        """Learn from user interactions to improve knowledge base"""
        try:
            # Only add knowledge if user feedback is positive
            if user_feedback and user_feedback.get('rating', 0) >= 4:
                # Create knowledge document from successful interaction
                document = KnowledgeDocument(
                    id=f"interaction_{datetime.now().timestamp()}",
                    title=f"User Query: {user_query[:50]}...",
                    content=f"Query: {user_query}\n\nResponse: {agent_response}",
                    document_type=DocumentType.FAQ,
                    skill_level=SkillLevel.ALL_LEVELS,
                    tags=['user-interaction', 'faq'],
                    metadata={
                        'source': 'user_interaction',
                        'user_rating': user_feedback.get('rating'),
                        'interaction_date': datetime.now().isoformat()
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    source='user_interaction',
                    confidence_score=0.8
                )
                
                # Add to knowledge base
                success = self.knowledge_base.add_document(document)
                if success:
                    # Add to vector store
                    self.vector_store.add_document_embedding(document)
                    self.logger.info(f"Added knowledge from user interaction: {document.id}")
        
        except Exception as e:
            self.logger.error(f"Error adding knowledge from interaction: {e}")
    
    def get_rag_statistics(self) -> Dict[str, Any]:
        """Get comprehensive RAG system statistics"""
        return {
            'rag_orchestrator_stats': self.rag_stats,
            'knowledge_base_stats': self.knowledge_base.get_statistics(),
            'vector_store_stats': self.vector_store.get_statistics(),
            'retrieval_agent_stats': self.retrieval_agent.get_status(),
            'cache_stats': {
                'response_cache_size': len(self.response_cache),
                'cache_hit_rate': self.rag_stats.get('cache_hits', 0) / max(self.rag_stats.get('total_rag_requests', 1), 1)
            },
            'configuration': self.rag_config
        }
    
    def update_rag_config(self, new_config: Dict[str, Any]):
        """Update RAG configuration"""
        self.rag_config.update(new_config)
        self.logger.info(f"Updated RAG configuration: {new_config}")
    
    async def rebuild_knowledge_index(self):
        """Rebuild the entire knowledge index"""
        try:
            self.logger.info("Rebuilding knowledge index...")
            
            # Get all documents
            documents = list(self.knowledge_base.documents.values())
            
            # Rebuild vector store
            success = self.vector_store.rebuild_index(documents)
            
            if success:
                # Clear caches
                self.response_cache.clear()
                self.retrieval_agent.query_cache.clear()
                
                self.logger.info(f"Successfully rebuilt knowledge index with {len(documents)} documents")
            else:
                self.logger.error("Failed to rebuild knowledge index")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error rebuilding knowledge index: {e}")
            return False
