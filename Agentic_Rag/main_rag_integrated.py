import os
import sys
# DON'T CHANGE: Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add project root to sys.path for src imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import logging
from datetime import datetime

# Import existing components
from src.routes.agents import agents_bp
from src.routes.auth import auth_bp
from src.models.poker_models import db, User, HandAnalysis, LearningProgress, CommunityPost
from src.websockets.chat_handler import create_websocket_handlers

# Import RAG components
from Agentic_Rag.rag.knowledge_base import PokerKnowledgeBase
from Agentic_Rag.rag.vector_store import VectorStore, EmbeddingService
from Agentic_Rag.rag.retrieval_agent import RetrievalAgent
from Agentic_Rag.rag.rag_orchestrator import RAGOrchestrator
from Agentic_Rag.rag.knowledge_sources import KnowledgeSourceManager
from Agentic_Rag.rag_routes import rag_bp, init_rag_routes
from src.routes.chat_routes import chat_bp

# Import enhanced agents
from src.agents.coach import CoachAgent
from src.models.orchestrator import AgentOrchestrator

from sqlalchemy import text

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application with RAG integration"""
    app = Flask(__name__)

    # --- API Monitoring: Log requests, response time, and exceptions ---
    import time
    from flask import request, g

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        if hasattr(g, "start_time"):
            duration = (time.time() - g.start_time) * 1000  # ms
        else:
            duration = -1
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        logger.info(
            f"API Request: {request.method} {request.path} from {ip} | Status: {response.status_code} | Time: {duration:.2f}ms"
        )
        return response

    @app.teardown_request
    def log_exception(exc):
        if exc is not None:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            logger.error(
                f"Exception during request: {request.method} {request.path} from {ip} | Error: {exc}",
                exc_info=True,
            )

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pokerpy.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    
    # Initialize extensions
    CORS(app, origins="*")
    db.init_app(app)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Initialize RAG system
    logger.info("Initializing RAG system...")
    
    # Create RAG components
    knowledge_base = PokerKnowledgeBase(storage_path="/tmp/poker_knowledge.json")
    embedding_service = EmbeddingService(model_name="tfidf", cache_embeddings=True)
    vector_store = VectorStore(storage_path="/tmp/vector_store.db", embedding_service=embedding_service)
    
    # Initialize vector store with existing knowledge
    documents = list(knowledge_base.documents.values())
    if documents:
        vector_store.rebuild_index(documents)
        logger.info(f"Initialized vector store with {len(documents)} documents")
    
    # Create agent orchestrator
    agent_orchestrator = AgentOrchestrator()
    
    # Create RAG orchestrator
    rag_orchestrator = RAGOrchestrator(
        agent_orchestrator=agent_orchestrator,
        knowledge_base=knowledge_base,
        vector_store=vector_store
    )
    
    # Create knowledge source manager
    knowledge_source_manager = KnowledgeSourceManager(knowledge_base, vector_store)
    
    # Create enhanced agents
    rag_coach = CoachAgent(rag_orchestrator)
    agent_orchestrator.register_agent(rag_coach)
    
    # Store RAG components in app context
    app.rag_orchestrator = rag_orchestrator
    app.knowledge_source_manager = knowledge_source_manager
    app.agent_orchestrator = agent_orchestrator
    
    # Initialize RAG routes
    init_rag_routes(rag_orchestrator, knowledge_source_manager)
    
    # Register blueprints
    app.register_blueprint(agents_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(chat_bp)
    
    # Initialize WebSocket handlers
    create_websocket_handlers(socketio)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
        
        # Initialize knowledge base with existing documents
        logger.info("Knowledge sources initialized")
    
    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def api_health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            db.session.execute(text('SELECT 1'))

            # Check RAG system
            rag_health = {
                'knowledge_base_documents': len(knowledge_base.documents),
                'vector_store_vectors': len(vector_store.vectors),
                'registered_agents': len(agent_orchestrator.agents),
                'knowledge_sources': len(knowledge_source_manager.sources)
            }

            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'rag_system': rag_health,
                'version': '1.0.0-rag'
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    # Root endpoint
    @app.route('/')
    def index():
        """Root endpoint"""
        return jsonify({
            'message': 'PokerPy RAG-Enhanced Backend API',
            'version': '1.0.0-rag',
            'features': [
                'Agentic AI System',
                'RAG Knowledge Retrieval',
                'Real-time WebSocket Communication',
                'Poker Hand Analysis',
                'AI Coaching',
                'Learning Path Generation',
                'Community Features'
            ],
            'endpoints': {
                'health': '/health',
                'agents': '/api/agents',
                'auth': '/api/auth',
                'rag': '/api/rag',
                'websocket': '/socket.io'
            },
            'timestamp': datetime.now().isoformat()
        })
    
    # Initialize knowledge base with content from sources on startup
    def initialize_knowledge():
        """Initialize knowledge base with content from sources"""
        try:
            import asyncio
            
            # Run knowledge ingestion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    knowledge_source_manager.ingest_from_all_sources()
                )
                logger.info(f"Knowledge ingestion completed: {result}")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error initializing knowledge: {e}")
    
    # Run knowledge initialization after app creation
    with app.app_context():
        initialize_knowledge()
    
    logger.info("PokerPy RAG-Enhanced Backend initialized successfully")
    return app, socketio

def main():
    """Main entry point"""
    app, socketio = create_app()
    
    # Get configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting PokerPy RAG-Enhanced Backend on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("Available endpoints:")
    logger.info("  - Health check: /api/health")
    logger.info("  - Agents API: /api/agents")
    logger.info("  - Authentication: /api/auth")
    logger.info("  - RAG System: /api/rag")
    logger.info("  - WebSocket: /socket.io")
    
    # Run the application
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )
    logger.info("PokerPy RAG-Enhanced Backend is running...")
if __name__ == '__main__':
    main()
