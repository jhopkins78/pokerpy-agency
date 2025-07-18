"""
Retrieval Agent and Query Processing for Poker RAG System
Handles intelligent knowledge retrieval and query understanding
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

from src.agents.base_agent import BaseAgent, AgentMessage, AgentStatus
from Agentic_Rag.rag.knowledge_base import PokerKnowledgeBase, KnowledgeDocument, DocumentType, SkillLevel
from .vector_store import VectorStore, EmbeddingService

class QueryType(Enum):
    """Types of queries the system can handle"""
    STRATEGY_QUESTION = "strategy_question"
    RULE_CLARIFICATION = "rule_clarification"
    HAND_ANALYSIS = "hand_analysis"
    CONCEPT_EXPLANATION = "concept_explanation"
    LEARNING_REQUEST = "learning_request"
    GENERAL_QUESTION = "general_question"

class QueryIntent(Enum):
    """Intent behind the query"""
    LEARN = "learn"
    ANALYZE = "analyze"
    CLARIFY = "clarify"
    IMPROVE = "improve"
    COMPARE = "compare"
    EXPLAIN = "explain"

@dataclass
class ProcessedQuery:
    """Represents a processed and analyzed query"""
    original_query: str
    query_type: QueryType
    intent: QueryIntent
    skill_level: SkillLevel
    extracted_entities: Dict[str, List[str]]
    keywords: List[str]
    context: Dict[str, Any]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'original_query': self.original_query,
            'query_type': self.query_type.value,
            'intent': self.intent.value,
            'skill_level': self.skill_level.value,
            'extracted_entities': self.extracted_entities,
            'keywords': self.keywords,
            'context': self.context,
            'confidence': self.confidence
        }

@dataclass
class RetrievalResult:
    """Represents the result of a knowledge retrieval"""
    query: ProcessedQuery
    retrieved_documents: List[KnowledgeDocument]
    similarity_scores: List[float]
    total_results: int
    retrieval_time: float
    metadata: Dict[str, Any]
    
    def get_top_documents(self, n: int = 3) -> List[KnowledgeDocument]:
        """Get top N most relevant documents"""
        return self.retrieved_documents[:n]
    
    def get_documents_by_type(self, doc_type: DocumentType) -> List[KnowledgeDocument]:
        """Get documents of specific type"""
        return [doc for doc in self.retrieved_documents if doc.document_type == doc_type]

class QueryProcessor:
    """
    Processes and analyzes user queries to understand intent and extract entities
    """
    
    def __init__(self):
        self.logger = logging.getLogger("query_processor")
        
        # Poker-specific entity patterns
        self.entity_patterns = {
            'positions': r'\b(button|cutoff|hijack|under the gun|utg|big blind|bb|small blind|sb|early position|late position|middle position)\b',
            'hands': r'\b([AKQJT2-9]{2}[so]?|pocket [a-z]+|[AKQJT2-9][AKQJT2-9])\b',
            'actions': r'\b(fold|call|raise|bet|check|all-in|shove)\b',
            'betting_rounds': r'\b(preflop|flop|turn|river)\b',
            'game_types': r'\b(texas hold\'?em|omaha|stud|tournament|cash game|sit and go|sng)\b',
            'concepts': r'\b(pot odds|equity|implied odds|reverse implied odds|expected value|ev|gto|exploitative|range|bluff|value bet|continuation bet|c-bet)\b'
        }
        
        # Query type indicators
        self.query_type_indicators = {
            QueryType.STRATEGY_QUESTION: [
                'should i', 'what should', 'how to', 'when to', 'strategy', 'optimal', 'best play'
            ],
            QueryType.RULE_CLARIFICATION: [
                'rule', 'legal', 'allowed', 'can i', 'is it', 'what happens if', 'how does'
            ],
            QueryType.HAND_ANALYSIS: [
                'analyze', 'review', 'what do you think', 'did i play', 'hand history', 'feedback'
            ],
            QueryType.CONCEPT_EXPLANATION: [
                'what is', 'explain', 'define', 'meaning', 'understand', 'concept', 'theory'
            ],
            QueryType.LEARNING_REQUEST: [
                'learn', 'study', 'improve', 'practice', 'teach me', 'help me get better'
            ]
        }
        
        # Intent indicators
        self.intent_indicators = {
            QueryIntent.LEARN: ['learn', 'study', 'understand', 'know', 'teach'],
            QueryIntent.ANALYZE: ['analyze', 'review', 'evaluate', 'assess', 'examine'],
            QueryIntent.CLARIFY: ['clarify', 'explain', 'what', 'how', 'why'],
            QueryIntent.IMPROVE: ['improve', 'better', 'fix', 'correct', 'optimize'],
            QueryIntent.COMPARE: ['compare', 'versus', 'vs', 'difference', 'better than'],
            QueryIntent.EXPLAIN: ['explain', 'tell me', 'describe', 'elaborate']
        }
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> ProcessedQuery:
        """Process and analyze a user query"""
        try:
            query_lower = query.lower()
            context = context or {}
            
            # Extract entities
            entities = self._extract_entities(query_lower)
            
            # Determine query type
            query_type = self._determine_query_type(query_lower)
            
            # Determine intent
            intent = self._determine_intent(query_lower)
            
            # Infer skill level from context or query complexity
            skill_level = self._infer_skill_level(query_lower, context)
            
            # Extract keywords
            keywords = self._extract_keywords(query_lower, entities)
            
            # Calculate confidence
            confidence = self._calculate_confidence(query_type, intent, entities)
            
            processed_query = ProcessedQuery(
                original_query=query,
                query_type=query_type,
                intent=intent,
                skill_level=skill_level,
                extracted_entities=entities,
                keywords=keywords,
                context=context,
                confidence=confidence
            )
            
            self.logger.info(f"Processed query: {query_type.value} with confidence {confidence:.2f}")
            return processed_query
        
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            # Return default processed query
            return ProcessedQuery(
                original_query=query,
                query_type=QueryType.GENERAL_QUESTION,
                intent=QueryIntent.CLARIFY,
                skill_level=SkillLevel.BEGINNER,
                extracted_entities={},
                keywords=query.lower().split(),
                context=context or {},
                confidence=0.5
            )
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract poker-specific entities from query"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates
        
        return entities
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query based on indicators"""
        scores = {}
        
        for query_type, indicators in self.query_type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in query)
            scores[query_type] = score
        
        # Return type with highest score, default to general question
        if scores:
            return max(scores, key=scores.get)
        return QueryType.GENERAL_QUESTION
    
    def _determine_intent(self, query: str) -> QueryIntent:
        """Determine the intent behind the query"""
        scores = {}
        
        for intent, indicators in self.intent_indicators.items():
            score = sum(1 for indicator in indicators if indicator in query)
            scores[intent] = score
        
        # Return intent with highest score, default to clarify
        if scores:
            return max(scores, key=scores.get)
        return QueryIntent.CLARIFY
    
    def _infer_skill_level(self, query: str, context: Dict[str, Any]) -> SkillLevel:
        """Infer user skill level from query and context"""
        # Check context first
        if 'skill_level' in context:
            try:
                return SkillLevel(context['skill_level'])
            except ValueError:
                pass
        
        # Analyze query complexity
        advanced_terms = ['gto', 'exploitative', 'range', 'equity', 'ev', 'implied odds', 'reverse implied odds']
        intermediate_terms = ['pot odds', 'position', 'continuation bet', 'c-bet', 'value bet']
        
        advanced_count = sum(1 for term in advanced_terms if term in query)
        intermediate_count = sum(1 for term in intermediate_terms if term in query)
        
        if advanced_count >= 2:
            return SkillLevel.ADVANCED
        elif advanced_count >= 1 or intermediate_count >= 2:
            return SkillLevel.INTERMEDIATE
        else:
            return SkillLevel.BEGINNER
    
    def _extract_keywords(self, query: str, entities: Dict[str, List[str]]) -> List[str]:
        """Extract relevant keywords from query"""
        # Start with all entities
        keywords = []
        for entity_list in entities.values():
            keywords.extend(entity_list)
        
        # Add important words from query
        words = query.split()
        important_words = [word for word in words if len(word) > 3 and word not in ['what', 'when', 'where', 'should', 'would', 'could']]
        keywords.extend(important_words)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def _calculate_confidence(self, query_type: QueryType, intent: QueryIntent, entities: Dict[str, List[str]]) -> float:
        """Calculate confidence score for the query processing"""
        base_confidence = 0.5
        
        # Boost confidence if we found entities
        if entities:
            base_confidence += 0.2
        
        # Boost confidence if query type is not general
        if query_type != QueryType.GENERAL_QUESTION:
            base_confidence += 0.2
        
        # Boost confidence if intent is specific
        if intent != QueryIntent.CLARIFY:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

class RetrievalAgent(BaseAgent):
    """
    Specialized agent for knowledge retrieval and RAG processing
    Inherits from BaseAgent to integrate with the existing agent system
    """
    
    def __init__(self, knowledge_base: PokerKnowledgeBase = None, vector_store: VectorStore = None):
        super().__init__(
            agent_id="retrieval_agent",
            name="Knowledge Retrieval Agent",
            description="Retrieves relevant poker knowledge for RAG-enhanced responses"
        )
        
        self.knowledge_base = knowledge_base or PokerKnowledgeBase()
        self.vector_store = vector_store or VectorStore()
        self.query_processor = QueryProcessor()
        
        # Initialize vector store with knowledge base documents
        self._initialize_vector_store()
        
        # Performance metrics
        self.retrieval_stats = {
            'total_queries': 0,
            'successful_retrievals': 0,
            'average_retrieval_time': 0.0,
            'cache_hits': 0
        }
        
        # Simple cache for frequent queries
        self.query_cache = {}
        self.cache_size_limit = 100
    
    def _initialize_vector_store(self):
        """Initialize vector store with knowledge base documents"""
        try:
            documents = list(self.knowledge_base.documents.values())
            if documents:
                self.vector_store.rebuild_index(documents)
                self.logger.info(f"Initialized vector store with {len(documents)} documents")
        except Exception as e:
            self.logger.error(f"Error initializing vector store: {e}")
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process retrieval requests"""
        try:
            if message.message_type == "retrieve_knowledge":
                return await self._handle_knowledge_retrieval(message)
            elif message.message_type == "add_knowledge":
                return await self._handle_add_knowledge(message)
            elif message.message_type == "update_knowledge":
                return await self._handle_update_knowledge(message)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    async def _handle_knowledge_retrieval(self, message: AgentMessage) -> AgentMessage:
        """Handle knowledge retrieval requests"""
        start_time = datetime.now()
        
        try:
            content = message.content
            query = content.get('query', '')
            context = content.get('context', {})
            max_results = content.get('max_results', 5)
            min_similarity = content.get('min_similarity', 0.1)
            
            # Check cache first
            cache_key = f"{query}_{max_results}_{min_similarity}"
            if cache_key in self.query_cache:
                self.retrieval_stats['cache_hits'] += 1
                cached_result = self.query_cache[cache_key]
                return self._create_response(message, cached_result)
            
            # Process query
            processed_query = self.query_processor.process_query(query, context)
            
            # Retrieve relevant documents using vector similarity
            similar_docs = self.vector_store.search_similar(
                query=query,
                top_k=max_results,
                min_similarity=min_similarity,
                filters={
                    'skill_level': [processed_query.skill_level.value, SkillLevel.ALL_LEVELS.value]
                }
            )
            
            # Get full documents
            retrieved_documents = []
            similarity_scores = []
            
            for doc_id, similarity in similar_docs:
                document = self.knowledge_base.get_document(doc_id)
                if document:
                    retrieved_documents.append(document)
                    similarity_scores.append(similarity)
            
            # Create retrieval result
            retrieval_time = (datetime.now() - start_time).total_seconds()
            
            result = RetrievalResult(
                query=processed_query,
                retrieved_documents=retrieved_documents,
                similarity_scores=similarity_scores,
                total_results=len(retrieved_documents),
                retrieval_time=retrieval_time,
                metadata={
                    'vector_search_results': len(similar_docs),
                    'filtered_results': len(retrieved_documents),
                    'query_confidence': processed_query.confidence
                }
            )
            
            # Update stats
            self.retrieval_stats['total_queries'] += 1
            self.retrieval_stats['successful_retrievals'] += 1
            self.retrieval_stats['average_retrieval_time'] = (
                (self.retrieval_stats['average_retrieval_time'] * (self.retrieval_stats['total_queries'] - 1) + retrieval_time)
                / self.retrieval_stats['total_queries']
            )
            
            # Cache result if cache is not full
            if len(self.query_cache) < self.cache_size_limit:
                self.query_cache[cache_key] = result
            
            # Prepare response
            response_content = {
                'retrieval_result': {
                    'processed_query': processed_query.to_dict(),
                    'documents': [doc.to_dict() for doc in retrieved_documents],
                    'similarity_scores': similarity_scores,
                    'total_results': len(retrieved_documents),
                    'retrieval_time': retrieval_time,
                    'metadata': result.metadata
                },
                'success': True
            }
            
            return self._create_response(message, response_content)
        
        except Exception as e:
            self.logger.error(f"Error in knowledge retrieval: {e}")
            self.retrieval_stats['total_queries'] += 1
            return self._create_error_response(message, str(e))
    
    async def _handle_add_knowledge(self, message: AgentMessage) -> AgentMessage:
        """Handle adding new knowledge to the system"""
        try:
            content = message.content
            document_data = content.get('document')
            
            if not document_data:
                return self._create_error_response(message, "No document data provided")
            
            # Create knowledge document
            document = KnowledgeDocument.from_dict(document_data)
            
            # Add to knowledge base
            success = self.knowledge_base.add_document(document)
            
            if success:
                # Add to vector store
                self.vector_store.add_document_embedding(document)
                
                response_content = {
                    'success': True,
                    'document_id': document.id,
                    'message': 'Document added successfully'
                }
            else:
                response_content = {
                    'success': False,
                    'message': 'Failed to add document'
                }
            
            return self._create_response(message, response_content)
        
        except Exception as e:
            self.logger.error(f"Error adding knowledge: {e}")
            return self._create_error_response(message, str(e))
    
    async def _handle_update_knowledge(self, message: AgentMessage) -> AgentMessage:
        """Handle updating existing knowledge"""
        try:
            content = message.content
            document_id = content.get('document_id')
            updates = content.get('updates', {})
            
            if not document_id:
                return self._create_error_response(message, "No document ID provided")
            
            # Update in knowledge base
            success = self.knowledge_base.update_document(document_id, updates)
            
            if success:
                # Update in vector store
                document = self.knowledge_base.get_document(document_id)
                if document:
                    self.vector_store.update_embedding(document)
                
                # Clear cache
                self.query_cache.clear()
                
                response_content = {
                    'success': True,
                    'document_id': document_id,
                    'message': 'Document updated successfully'
                }
            else:
                response_content = {
                    'success': False,
                    'message': 'Failed to update document'
                }
            
            return self._create_response(message, response_content)
        
        except Exception as e:
            self.logger.error(f"Error updating knowledge: {e}")
            return self._create_error_response(message, str(e))
    
    def get_capabilities(self) -> List[Any]:
        """Return agent capabilities"""
        from src.agents.base_agent import AgentCapability
        return [
            AgentCapability(
                name="retrieve_knowledge", 
                description="Retrieve relevant knowledge documents",
                input_schema={"query": "str", "context": "dict", "max_results": "int"},
                output_schema={"retrieval_result": "dict", "success": "bool"}
            ),
            AgentCapability(
                name="add_knowledge", 
                description="Add new knowledge documents",
                input_schema={"document": "dict"},
                output_schema={"document_id": "str", "success": "bool"}
            ),
            AgentCapability(
                name="update_knowledge", 
                description="Update existing knowledge documents",
                input_schema={"document_id": "str", "updates": "dict"},
                output_schema={"success": "bool"}
            ),
            AgentCapability(
                name="search_knowledge", 
                description="Search knowledge base with advanced filters",
                input_schema={"query": "str", "filters": "dict"},
                output_schema={"results": "list", "success": "bool"}
            )
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics"""
        base_status = super().get_status()
        base_status.update({
            'knowledge_base_stats': self.knowledge_base.get_statistics(),
            'vector_store_stats': self.vector_store.get_statistics(),
            'retrieval_stats': self.retrieval_stats,
            'cache_size': len(self.query_cache)
        })
        return base_status
    
    def _create_response(self, original_message: AgentMessage, content: Any) -> AgentMessage:
        """Create response message"""
        return AgentMessage(
            id=f"response_{original_message.id}",
            sender=self.agent_id,
            recipient=original_message.sender,
            message_type=f"response_{original_message.message_type}",
            content=content,
            timestamp=datetime.now()
        )
    
    def _create_error_response(self, original_message: AgentMessage, error: str) -> AgentMessage:
        """Create error response message"""
        return AgentMessage(
            id=f"error_{original_message.id}",
            sender=self.agent_id,
            recipient=original_message.sender,
            message_type=f"error_{original_message.message_type}",
            content={
                'success': False,
                'error': error,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
