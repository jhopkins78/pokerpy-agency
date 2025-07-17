"""
Flask routes for RAG system endpoints
Provides API access to RAG functionality
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import logging

from rag.rag_orchestrator import RAGOrchestrator
from rag.knowledge_base import PokerKnowledgeBase, KnowledgeDocument, DocumentType, SkillLevel
from rag.vector_store import VectorStore, EmbeddingService
from Agentic_Rag.rag.retrieval_agent import RetrievalAgent
from rag.knowledge_sources import KnowledgeSourceManager

# Create blueprint
rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')

# Initialize RAG components (will be properly initialized in main.py)
rag_orchestrator = None
knowledge_source_manager = None

def init_rag_routes(app_rag_orchestrator, app_knowledge_source_manager):
    """Initialize RAG routes with orchestrator and source manager"""
    global rag_orchestrator, knowledge_source_manager
    rag_orchestrator = app_rag_orchestrator
    knowledge_source_manager = app_knowledge_source_manager

@rag_bp.route('/search', methods=['POST'])
def search_knowledge():
    """Search knowledge base with RAG capabilities"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', {})
        max_results = data.get('max_results', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Create retrieval message
        from agents.base_agent import AgentMessage
        
        retrieval_message = AgentMessage(
            id=f"search_{datetime.now().timestamp()}",
            sender="api",
            recipient="retrieval_agent",
            message_type="retrieve_knowledge",
            content={
                'query': query,
                'context': context,
                'max_results': max_results
            },
            timestamp=datetime.now()
        )
        
        # Process retrieval (sync wrapper for async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                rag_orchestrator.retrieval_agent.process_message(retrieval_message)
            )
        finally:
            loop.close()
        
        if response and response.content.get('success'):
            return jsonify({
                'success': True,
                'results': response.content['retrieval_result'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Search failed',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logging.error(f"Error in knowledge search: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/enhance', methods=['POST'])
def enhance_response():
    """Enhance an agent response with RAG"""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id', 'unknown')
        query = data.get('query', '')
        response = data.get('response', '')
        context = data.get('context', {})
        
        if not query or not response:
            return jsonify({'error': 'Query and response are required'}), 400
        
        # Enhance response (sync wrapper for async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            enhanced = loop.run_until_complete(
                rag_orchestrator.enhance_agent_response(agent_id, query, response, context)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'original_response': enhanced.original_response,
            'enhanced_response': enhanced.enhanced_response,
            'confidence_score': enhanced.confidence_score,
            'sources': enhanced.sources,
            'metadata': enhanced.metadata,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error enhancing response: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/knowledge', methods=['POST'])
def add_knowledge():
    """Add new knowledge to the system"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'content', 'document_type', 'skill_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create knowledge document
        document = KnowledgeDocument(
            id=data.get('id'),  # Will auto-generate if None
            title=data['title'],
            content=data['content'],
            document_type=DocumentType(data['document_type']),
            skill_level=SkillLevel(data['skill_level']),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=data.get('source', 'api'),
            author=data.get('author'),
            confidence_score=data.get('confidence_score', 0.8)
        )
        
        # Add to knowledge base
        success = rag_orchestrator.knowledge_base.add_document(document)
        
        if success:
            # Add to vector store
            rag_orchestrator.vector_store.add_document_embedding(document)
            
            return jsonify({
                'success': True,
                'document_id': document.id,
                'message': 'Knowledge added successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add knowledge',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logging.error(f"Error adding knowledge: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/knowledge/<document_id>', methods=['GET'])
def get_knowledge(document_id):
    """Get specific knowledge document"""
    try:
        document = rag_orchestrator.knowledge_base.get_document(document_id)
        
        if document:
            return jsonify({
                'success': True,
                'document': document.to_dict(),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Document not found',
                'timestamp': datetime.now().isoformat()
            }), 404
    
    except Exception as e:
        logging.error(f"Error getting knowledge: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/knowledge/<document_id>', methods=['PUT'])
def update_knowledge(document_id):
    """Update existing knowledge document"""
    try:
        data = request.get_json()
        
        # Update document
        success = rag_orchestrator.knowledge_base.update_document(document_id, data)
        
        if success:
            # Update vector store
            document = rag_orchestrator.knowledge_base.get_document(document_id)
            if document:
                rag_orchestrator.vector_store.update_embedding(document)
            
            return jsonify({
                'success': True,
                'document_id': document_id,
                'message': 'Knowledge updated successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update knowledge',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logging.error(f"Error updating knowledge: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/knowledge/<document_id>', methods=['DELETE'])
def delete_knowledge(document_id):
    """Delete knowledge document"""
    try:
        # Delete from knowledge base
        success = rag_orchestrator.knowledge_base.delete_document(document_id)
        
        if success:
            # Remove from vector store
            rag_orchestrator.vector_store.remove_embedding(document_id)
            
            return jsonify({
                'success': True,
                'document_id': document_id,
                'message': 'Knowledge deleted successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete knowledge',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logging.error(f"Error deleting knowledge: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/ingest', methods=['POST'])
def ingest_knowledge():
    """Ingest knowledge from sources"""
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        
        if source_id:
            # Ingest from specific source
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    knowledge_source_manager.ingest_from_source(source_id)
                )
            finally:
                loop.close()
        else:
            # Ingest from all sources
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    knowledge_source_manager.ingest_from_all_sources()
                )
            finally:
                loop.close()
        
        return jsonify({
            'success': True,
            'ingestion_result': result,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error ingesting knowledge: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/statistics', methods=['GET'])
def get_rag_statistics():
    """Get RAG system statistics"""
    try:
        stats = rag_orchestrator.get_rag_statistics()
        source_stats = knowledge_source_manager.get_source_statistics()
        
        return jsonify({
            'success': True,
            'rag_statistics': stats,
            'source_statistics': source_stats,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error getting statistics: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/rebuild-index', methods=['POST'])
def rebuild_index():
    """Rebuild the knowledge index"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                rag_orchestrator.rebuild_knowledge_index()
            )
        finally:
            loop.close()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Knowledge index rebuilt successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to rebuild index',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logging.error(f"Error rebuilding index: {e}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/health', methods=['GET'])
def rag_health():
    """RAG system health check"""
    try:
        health_status = {
            'rag_orchestrator': rag_orchestrator is not None,
            'knowledge_base': len(rag_orchestrator.knowledge_base.documents) if rag_orchestrator else 0,
            'vector_store': len(rag_orchestrator.vector_store.vectors) if rag_orchestrator else 0,
            'knowledge_sources': len(knowledge_source_manager.sources) if knowledge_source_manager else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
    
    except Exception as e:
        logging.error(f"Error in health check: {e}")
        return jsonify({'error': str(e)}), 500
