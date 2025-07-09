# PokerPy Agentic Backend - Deployment Guide

## 🏗️ Architecture Overview

The PokerPy backend is built using the **Harmony Engine architecture** with specialized AI agents working together to provide comprehensive poker coaching and community features.

### Core Components

1. **Agent Orchestrator** - Coordinates communication between agents
2. **Hand Analyzer Agent** - Technical poker analysis with GTO insights
3. **AI Coach Agent** - Plain English explanations and personalized coaching
4. **Learning Path Agent** - Adaptive curriculum and progress tracking
5. **Community Agent** - Social features with moderation and reputation
6. **WebSocket Handlers** - Real-time chat and live updates
7. **Authentication System** - JWT-based user management
8. **Database Models** - Comprehensive data structures for all features

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip3
- Git

### Local Development

1. **Clone and Setup**
   ```bash
   cd pokerpy-backend
   pip3 install -r requirements.txt
   ```

2. **Run the Backend**
   ```bash
   python3 src/main.py
   ```

3. **Access the API**
   - Backend: http://localhost:5000
   - API Documentation: http://localhost:5000
   - Health Check: http://localhost:5000/api/health

## 📦 Production Deployment

### Option 1: Using Manus Service Deployment

```bash
# Deploy using Manus service deployment tool
manus-deploy-backend pokerpy-backend flask
```

### Option 2: Manual Deployment with Gunicorn

1. **Install Production Dependencies**
   ```bash
   pip3 install gunicorn eventlet
   ```

2. **Create Production Configuration**
   ```bash
   # Create .env file
   echo "FLASK_ENV=production" > .env
   echo "SECRET_KEY=your-production-secret-key" >> .env
   echo "DATABASE_URL=your-production-database-url" >> .env
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 src.main:app
   ```

### Option 3: Docker Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY src/ ./src/
   
   EXPOSE 5000
   CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "src.main:app"]
   ```

2. **Build and Run**
   ```bash
   docker build -t pokerpy-backend .
   docker run -p 5000:5000 pokerpy-backend
   ```

## 🔗 API Endpoints

### System Endpoints

- `GET /api/health` - Health check
- `GET /api/system/stats` - System statistics

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### AI Agents

- `GET /api/agents/health` - Agents health check
- `POST /api/agents/analyze-hand` - Analyze poker hands
- `POST /api/agents/ask-coach` - Ask AI coach questions
- `POST /api/agents/learning-path` - Create learning paths
- `POST /api/agents/learning-progress` - Track learning progress
- `POST /api/agents/equity-calculator` - Calculate hand equity
- `POST /api/agents/identify-leaks` - Identify poker leaks
- `POST /api/agents/encouragement` - Get motivational coaching

### Community

- `POST /api/agents/community/posts` - Create community posts
- `GET /api/agents/community/feed` - Get community feed

### Workflows

- `POST /api/agents/workflow/analyze_and_coach` - Run analysis + coaching workflow
- `POST /api/agents/workflow/full_analysis` - Run complete analysis workflow

## 🔌 WebSocket Events

### Chat Events

- `connect` - Connect to AI coach chat
- `disconnect` - Disconnect from chat
- `chat_message` - Send message to AI coach
- `coach_response` - Receive coach response
- `coach_typing` - Typing indicator

### Live Analysis Events

- `analyze_hand_live` - Start live hand analysis
- `analysis_started` - Analysis started notification
- `analysis_progress` - Progress updates
- `analysis_complete` - Analysis completed
- `analysis_error` - Analysis error

### Community Events

- `join_community` - Join community updates
- `new_post` - New community post notification
- `new_comment` - New comment notification

## 📊 Database Schema

### Core Tables

- **users** - User accounts and preferences
- **user_reputations** - Community reputation tracking
- **hand_analyses** - Stored hand analysis results
- **learning_modules** - Curriculum content
- **learning_progress** - User progress tracking
- **community_posts** - Community posts and discussions
- **comments** - Post comments and replies
- **user_sessions** - Session tracking for analytics

## 🔐 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- CORS enabled for frontend communication
- Input validation and sanitization
- Rate limiting (configurable)
- Content moderation for community features

## 🤖 Agent System Details

### Hand Analyzer Agent

**Capabilities:**
- `analyze_hand` - Comprehensive hand analysis
- `calculate_equity` - Hand equity calculations
- `identify_leaks` - Pattern recognition for common mistakes
- `generate_scenarios` - Alternative scenario analysis

**Input Format:**
```json
{
  "hand_history": "PokerStars Hand #...",
  "player_position": "BTN",
  "stack_size": 100.0,
  "analysis_depth": "basic"
}
```

### AI Coach Agent

**Capabilities:**
- `answer_question` - Conversational Q&A
- `explain_analysis` - Plain English explanations
- `provide_encouragement` - Motivational coaching
- `suggest_improvements` - Personalized recommendations

**Features:**
- Adaptive communication style
- Skill-level appropriate explanations
- Encouraging tone and positive reinforcement
- Follow-up question suggestions

### Learning Path Agent

**Capabilities:**
- `create_learning_path` - Personalized curriculum
- `track_progress` - Progress monitoring
- `assess_skill_level` - Skill assessment
- `recommend_next_steps` - Adaptive recommendations

**Features:**
- Prerequisite tracking
- Achievement system
- Adaptive difficulty
- Progress analytics

### Community Agent

**Capabilities:**
- `create_post` - Post creation with moderation
- `get_community_feed` - Personalized feed generation
- `moderate_content` - Automated content moderation
- `manage_user_reputation` - Reputation system
- `generate_insights` - Community analytics

**Features:**
- Auto-moderation with confidence scoring
- Reputation-based privileges
- Trending topic detection
- Engagement analytics

## 🔄 Workflow System

The orchestrator supports predefined workflows that chain multiple agents:

### Available Workflows

1. **analyze_and_coach** - Hand analysis + coaching explanation
2. **full_analysis** - Complete analysis with learning recommendations

### Custom Workflow Example

```python
# Define custom workflow
orchestrator.define_workflow("custom_workflow", [
    "hand_analyzer",
    "coach", 
    "learning_path"
])

# Execute workflow
result = await orchestrator.execute_workflow("custom_workflow", data, user_id)
```

## 📈 Monitoring and Analytics

### Health Monitoring

- Agent status monitoring
- Database connection health
- WebSocket connection tracking
- Performance metrics

### Analytics Features

- User engagement tracking
- Learning progress analytics
- Community activity metrics
- System performance monitoring

## 🛠️ Configuration

### Environment Variables

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
DEBUG=False

# Database
DATABASE_URL=sqlite:///app.db

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=24  # hours
JWT_REFRESH_TOKEN_EXPIRES=720  # hours (30 days)

# AI Configuration (for future enhancements)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Redis (for caching and rate limiting)
REDIS_URL=redis://localhost:6379

# Monitoring
PROMETHEUS_ENABLED=true
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip3 install pytest pytest-flask pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### API Testing

```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test agent health
curl http://localhost:5000/api/agents/health

# Test hand analysis
curl -X POST http://localhost:5000/api/agents/analyze-hand \
  -H "Content-Type: application/json" \
  -d '{"hand_history": "Sample hand history", "user_id": "test"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

2. **Database Issues**
   - Verify database file permissions
   - Check SQLAlchemy configuration

3. **WebSocket Connection Issues**
   - Verify CORS configuration
   - Check firewall settings

4. **Agent Communication Errors**
   - Check agent initialization
   - Verify message format

### Debug Mode

```bash
# Run with debug logging
FLASK_DEBUG=1 python3 src/main.py
```

## 📚 Integration Guide

### Frontend Integration

1. **Authentication Flow**
   ```javascript
   // Register user
   const response = await fetch('/api/auth/register', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ username, email, password })
   });
   
   // Store JWT token
   const { access_token } = await response.json();
   localStorage.setItem('token', access_token);
   ```

2. **WebSocket Connection**
   ```javascript
   import io from 'socket.io-client';
   
   const socket = io('http://localhost:5000', {
     auth: { user_id: 'user123' }
   });
   
   // Listen for coach responses
   socket.on('coach_response', (data) => {
     console.log('Coach says:', data.message);
   });
   
   // Send message to coach
   socket.emit('chat_message', { 
     message: 'How should I play pocket aces?' 
   });
   ```

3. **API Calls with Authentication**
   ```javascript
   const token = localStorage.getItem('token');
   
   const response = await fetch('/api/agents/analyze-hand', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'Authorization': `Bearer ${token}`
     },
     body: JSON.stringify({ hand_history: '...' })
   });
   ```

## 🚀 Scaling Considerations

### Horizontal Scaling

- Use Redis for session storage
- Implement database connection pooling
- Use load balancer for multiple instances
- Consider microservices architecture for agents

### Performance Optimization

- Implement caching for frequent queries
- Use background tasks for heavy computations
- Optimize database queries
- Implement rate limiting

### Production Recommendations

- Use PostgreSQL for production database
- Implement proper logging and monitoring
- Set up automated backups
- Use environment-specific configurations
- Implement health checks and auto-recovery

## 📞 Support

For technical support or questions about the agentic system:

1. Check the API documentation at the root URL
2. Review the health check endpoints
3. Check agent status via `/api/agents/health`
4. Monitor WebSocket connections
5. Review application logs

---

**Built with Harmony Engine Architecture** 🤖

*The PokerPy agentic backend provides a comprehensive foundation for AI-powered poker coaching with real-time features, community interaction, and personalized learning paths.*

