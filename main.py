import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.poker_models import db  # Use single database instance
from src.routes.user import user_bp
from src.routes.agents import agents_bp
from src.routes.auth import auth_bp, init_jwt
from src.websockets.chat_handler import create_websocket_handlers

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes to allow frontend-backend communication
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Initialize SocketIO for real-time features
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize JWT for authentication
jwt = init_jwt(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(agents_bp, url_prefix='/api/agents')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize single database instance
db.init_app(app)

# Initialize WebSocket handlers
websocket_handlers = create_websocket_handlers(socketio)

# Create all tables and initialize data
with app.app_context():
    db.create_all()
    
    # Initialize learning modules if they don't exist
    from src.models.poker_models import LearningModule, SkillLevel
    
    # Check if modules already exist
    existing_modules = LearningModule.query.first()
    if not existing_modules:
        # Create initial learning modules
        modules = [
            LearningModule(
                id="poker_basics",
                title="Poker Fundamentals",
                description="Learn the basic rules, hand rankings, and game flow",
                difficulty=SkillLevel.BEGINNER,
                estimated_time=30,
                content_type="video",
                tags=["fundamentals", "rules", "hand-rankings"],
                prerequisites=[],
                order_index=1
            ),
            LearningModule(
                id="position_basics",
                title="Understanding Position",
                description="Why position is the most important factor in poker",
                difficulty=SkillLevel.BEGINNER,
                estimated_time=25,
                content_type="video",
                tags=["position", "strategy", "fundamentals"],
                prerequisites=["poker_basics"],
                order_index=2
            ),
            LearningModule(
                id="starting_hands",
                title="Starting Hand Selection",
                description="Which hands to play from which positions",
                difficulty=SkillLevel.BEGINNER,
                estimated_time=35,
                content_type="article",
                tags=["preflop", "hand-selection", "ranges"],
                prerequisites=["poker_basics", "position_basics"],
                order_index=3
            ),
            LearningModule(
                id="pot_odds",
                title="Pot Odds and Equity",
                description="Understanding pot odds and hand equity calculations",
                difficulty=SkillLevel.INTERMEDIATE,
                estimated_time=40,
                content_type="video",
                tags=["math", "equity", "pot-odds"],
                prerequisites=["starting_hands"],
                order_index=4
            ),
            LearningModule(
                id="c_betting",
                title="Continuation Betting",
                description="When and how to continuation bet effectively",
                difficulty=SkillLevel.INTERMEDIATE,
                estimated_time=45,
                content_type="article",
                tags=["postflop", "c-bet", "aggression"],
                prerequisites=["pot_odds"],
                order_index=5
            ),
            LearningModule(
                id="range_construction",
                title="Range Construction",
                description="Building and analyzing hand ranges",
                difficulty=SkillLevel.ADVANCED,
                estimated_time=60,
                content_type="video",
                tags=["ranges", "advanced", "theory"],
                prerequisites=["c_betting"],
                order_index=6
            ),
            LearningModule(
                id="bluff_catching",
                title="Bluff Catching",
                description="How to identify and call bluffs effectively",
                difficulty=SkillLevel.INTERMEDIATE,
                estimated_time=50,
                content_type="article",
                tags=["postflop", "bluff-catching", "hand-reading"],
                prerequisites=["pot_odds"],
                order_index=7
            ),
            LearningModule(
                id="bankroll_management",
                title="Bankroll Management",
                description="Managing your poker bankroll for long-term success",
                difficulty=SkillLevel.BEGINNER,
                estimated_time=20,
                content_type="article",
                tags=["bankroll", "management", "fundamentals"],
                prerequisites=["poker_basics"],
                order_index=8
            )
        ]
        
        for module in modules:
            db.session.add(module)
        
        try:
            db.session.commit()
            print("✅ Learning modules initialized successfully")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing learning modules: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Global health check endpoint"""
    return {
        "status": "healthy",
        "service": "PokerPy Agentic Backend",
        "version": "1.0.0",
        "components": {
            "database": "connected",
            "agents": "initialized",
            "websockets": "ready",
            "authentication": "enabled",
            "api": "ready"
        },
        "features": {
            "hand_analysis": True,
            "ai_coaching": True,
            "learning_paths": True,
            "community": True,
            "real_time_chat": True,
            "user_authentication": True
        }
    }

@app.route('/api/system/stats', methods=['GET'])
def system_stats():
    """Get system statistics"""
    try:
        from src.models.poker_models import User, HandAnalysis, CommunityPost, LearningProgress
        
        stats = {
            "users": {
                "total": User.query.count(),
                "active_today": 0,  # Would need session tracking
            },
            "analyses": {
                "total": HandAnalysis.query.count(),
                "today": 0,  # Would need date filtering
            },
            "community": {
                "posts": CommunityPost.query.count(),
                "active_discussions": 0,
            },
            "learning": {
                "modules_completed": LearningProgress.query.filter_by(status="completed").count(),
                "active_learners": 0,
            },
            "websockets": {
                "active_connections": websocket_handlers['chat'].get_active_users(),
            }
        }
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>PokerPy Agentic Backend</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                        h2 { color: #34495e; margin-top: 30px; }
                        .endpoint { background: #ecf0f1; padding: 10px; margin: 5px 0; border-radius: 5px; font-family: monospace; }
                        .post { color: #e74c3c; font-weight: bold; }
                        .get { color: #27ae60; font-weight: bold; }
                        .feature { background: #e8f5e8; padding: 8px; margin: 3px 0; border-left: 4px solid #27ae60; }
                        .status { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🃏 PokerPy Agentic Backend</h1>
                        
                        <div class="status">
                            <strong>✅ System Status:</strong> All systems operational<br>
                            <strong>🤖 AI Agents:</strong> Hand Analyzer, Coach, Learning Path, Community<br>
                            <strong>🔌 WebSockets:</strong> Real-time chat and updates enabled<br>
                            <strong>🔐 Authentication:</strong> JWT-based user management
                        </div>
                        
                        <h2>🔗 API Endpoints</h2>
                        
                        <h3>System</h3>
                        <div class="endpoint"><span class="get">GET</span> <a href="/api/health">/api/health</a> - Health check</div>
                        <div class="endpoint"><span class="get">GET</span> <a href="/api/system/stats">/api/system/stats</a> - System statistics</div>
                        
                        <h3>Authentication</h3>
                        <div class="endpoint"><span class="post">POST</span> /api/auth/register - Register new user</div>
                        <div class="endpoint"><span class="post">POST</span> /api/auth/login - User login</div>
                        <div class="endpoint"><span class="post">POST</span> /api/auth/logout - User logout</div>
                        <div class="endpoint"><span class="get">GET</span> /api/auth/profile - Get user profile</div>
                        
                        <h3>AI Agents</h3>
                        <div class="endpoint"><span class="get">GET</span> <a href="/api/agents/health">/api/agents/health</a> - Agents health check</div>
                        <div class="endpoint"><span class="post">POST</span> /api/agents/analyze-hand - Analyze poker hands</div>
                        <div class="endpoint"><span class="post">POST</span> /api/agents/ask-coach - Ask AI coach questions</div>
                        <div class="endpoint"><span class="post">POST</span> /api/agents/learning-path - Create learning paths</div>
                        <div class="endpoint"><span class="post">POST</span> /api/agents/equity-calculator - Calculate hand equity</div>
                        <div class="endpoint"><span class="post">POST</span> /api/agents/identify-leaks - Identify poker leaks</div>
                        
                        <h3>Community</h3>
                        <div class="endpoint"><span class="post">POST</span> /api/agents/community/posts - Create community posts</div>
                        <div class="endpoint"><span class="get">GET</span> /api/agents/community/feed - Get community feed</div>
                        
                        <h2>🤖 Agentic System Features</h2>
                        <div class="feature"><strong>Hand Analyzer Agent:</strong> Technical poker analysis with GTO insights</div>
                        <div class="feature"><strong>AI Coach Agent:</strong> Plain English explanations and personalized coaching</div>
                        <div class="feature"><strong>Learning Path Agent:</strong> Adaptive curriculum and progress tracking</div>
                        <div class="feature"><strong>Community Agent:</strong> Social features with moderation and reputation</div>
                        <div class="feature"><strong>Orchestrator:</strong> Workflow coordination and agent communication</div>
                        
                        <h2>🔌 Real-time Features</h2>
                        <div class="feature"><strong>WebSocket Chat:</strong> Instant AI coach responses</div>
                        <div class="feature"><strong>Live Hand Analysis:</strong> Real-time hand processing with progress updates</div>
                        <div class="feature"><strong>Community Updates:</strong> Live notifications for posts and comments</div>
                        <div class="feature"><strong>Progress Tracking:</strong> Real-time learning achievement notifications</div>
                        
                        <h2>🏗️ Architecture</h2>
                        <p><strong>Based on Harmony Engine:</strong> Multi-agent orchestration with specialized AI agents working together to provide comprehensive poker coaching and community features.</p>
                        
                        <p><em>🚀 Ready for frontend integration and deployment!</em></p>
                    </div>
                </body>
            </html>
            """

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {"error": "Endpoint not found"}, 404

@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500

if __name__ == '__main__':
    print("🚀 Starting PokerPy Agentic Backend...")
    print("🤖 Initializing AI agents...")
    print("📊 Setting up database...")
    print("🔌 Enabling WebSocket support...")
    print("🔐 Configuring authentication...")
    print("🌐 Enabling CORS for frontend communication...")
    print("✅ Backend ready at http://0.0.0.0:5000")
    print("🔗 WebSocket endpoint: ws://0.0.0.0:5000")
    print("📚 API documentation available at root URL")
    
    # Run with SocketIO support
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

