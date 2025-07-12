# PokerPy RAG-Enhanced Backend - Deployment Guide

## 🚀 Overview

This guide covers the deployment of the PokerPy RAG-Enhanced Backend, which integrates Retrieval-Augmented Generation (RAG) capabilities with the existing agentic poker coaching system.

## 📋 System Architecture

### RAG Components
- **Knowledge Base**: Stores poker strategy documents, hand analyses, and learning materials
- **Vector Store**: Provides semantic search capabilities using TF-IDF embeddings
- **Retrieval Agent**: Intelligent knowledge retrieval and query processing
- **RAG Orchestrator**: Coordinates knowledge retrieval with agent responses
- **Knowledge Sources**: Automated content ingestion from multiple sources

### Enhanced Agents
- **RAG-Enhanced Coach Agent**: Provides coaching with knowledge-backed responses
- **Retrieval Agent**: Specialized agent for knowledge retrieval operations
- **Knowledge Source Manager**: Manages automated content ingestion

## 🛠 Installation & Setup

### 1. Prerequisites
```bash
# Python 3.11+ required
python3 --version

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
```

### 2. Environment Setup
```bash
# Clone or navigate to project directory
cd pokerpy-backend

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key-here"
export JWT_SECRET_KEY="your-jwt-secret-here"
export DATABASE_URL="sqlite:///pokerpy_rag.db"
export FLASK_DEBUG="False"
export HOST="0.0.0.0"
export PORT="5000"
```

### 3. Database Setup
```bash
# The application will automatically create database tables on first run
# No manual database setup required for SQLite
```

## 🔧 Configuration

### RAG System Configuration
The RAG system is configured with the following default settings:

```python
# Knowledge Base Storage
KNOWLEDGE_BASE_PATH = "/tmp/poker_knowledge.json"

# Vector Store Configuration
VECTOR_STORE_PATH = "/tmp/vector_store.db"
EMBEDDING_MODEL = "tfidf"  # TF-IDF for fast, lightweight embeddings

# Knowledge Sources
- Poker Strategy Database (curated strategy content)
- Hand History Database (analyzed hands for learning)
- Community Content (high-quality discussions)
- Learning Materials (structured tutorials)
```

### Production Configuration
For production deployment, update the following:

```python
# Use persistent storage paths
KNOWLEDGE_BASE_PATH = "/var/lib/pokerpy/knowledge.json"
VECTOR_STORE_PATH = "/var/lib/pokerpy/vectors.db"

# Use PostgreSQL for production
DATABASE_URL = "postgresql://user:pass@localhost/pokerpy"

# Configure proper secret keys
SECRET_KEY = "your-production-secret-key"
JWT_SECRET_KEY = "your-production-jwt-key"
```

## 🚀 Running the Application

### Development Mode
```bash
# Run with RAG integration
python3 src/main_rag_integrated.py

# The application will start on http://0.0.0.0:5000
```

### Production Mode
```bash
# Using Gunicorn with eventlet for WebSocket support
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 src.main_rag_integrated:app

# Or using the production script
python3 src/main_rag_integrated.py
```

## 📡 API Endpoints

### Core Endpoints
- `GET /` - API information and health status
- `GET /health` - Detailed health check with RAG system status
- `POST /api/agents/*` - Agent communication endpoints
- `POST /api/auth/*` - Authentication endpoints
- `WebSocket /socket.io` - Real-time communication

### RAG-Specific Endpoints
- `POST /api/rag/search` - Search knowledge base
- `POST /api/rag/enhance` - Enhance responses with RAG
- `POST /api/rag/knowledge` - Add new knowledge
- `GET /api/rag/knowledge/<id>` - Get specific knowledge
- `PUT /api/rag/knowledge/<id>` - Update knowledge
- `DELETE /api/rag/knowledge/<id>` - Delete knowledge
- `POST /api/rag/ingest` - Trigger knowledge ingestion
- `GET /api/rag/statistics` - RAG system statistics
- `POST /api/rag/rebuild-index` - Rebuild vector index
- `GET /api/rag/health` - RAG system health check

## 🔍 Testing the RAG System

### 1. Health Check
```bash
curl http://localhost:5000/health
```

Expected response includes RAG system status:
```json
{
  "status": "healthy",
  "rag_system": {
    "knowledge_base_documents": 5,
    "vector_store_vectors": 5,
    "registered_agents": 2,
    "knowledge_sources": 4
  }
}
```

### 2. Knowledge Search
```bash
curl -X POST http://localhost:5000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "pot odds calculation",
    "max_results": 3
  }'
```

### 3. Enhanced Coaching
```bash
curl -X POST http://localhost:5000/api/agents/coach \
  -H "Content-Type: application/json" \
  -d '{
    "message_type": "coaching_request",
    "content": {
      "query": "How do I calculate pot odds?",
      "user_id": "test_user",
      "context": {"skill_level": "beginner"}
    }
  }'
```

## 📊 Monitoring & Maintenance

### RAG System Statistics
Monitor the RAG system performance:
```bash
curl http://localhost:5000/api/rag/statistics
```

### Knowledge Base Maintenance
```bash
# Trigger knowledge ingestion from all sources
curl -X POST http://localhost:5000/api/rag/ingest

# Rebuild vector index for better search performance
curl -X POST http://localhost:5000/api/rag/rebuild-index
```

### Log Monitoring
Key log messages to monitor:
- Knowledge base initialization
- Vector store operations
- Agent registration and capabilities
- Knowledge ingestion results
- RAG enhancement operations

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` or import issues
**Solution**: Ensure all dependencies are installed and Python path is correct
```bash
pip3 install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:/path/to/pokerpy-backend/src"
```

#### 2. Vector Store Issues
**Problem**: Vector search not working or slow performance
**Solution**: Rebuild the vector index
```bash
curl -X POST http://localhost:5000/api/rag/rebuild-index
```

#### 3. Knowledge Base Empty
**Problem**: No knowledge documents found
**Solution**: Trigger knowledge ingestion
```bash
curl -X POST http://localhost:5000/api/rag/ingest
```

#### 4. WebSocket Connection Issues
**Problem**: Real-time features not working
**Solution**: Ensure eventlet is installed and configured
```bash
pip3 install eventlet
# Use eventlet worker class with gunicorn
```

### Performance Optimization

#### 1. Vector Store Optimization
- Use FAISS for large-scale deployments (optional dependency)
- Implement periodic index rebuilding
- Monitor embedding cache performance

#### 2. Knowledge Base Optimization
- Implement document versioning
- Add content deduplication
- Optimize document chunking strategies

#### 3. Agent Performance
- Monitor agent response times
- Implement response caching
- Optimize RAG enhancement frequency

## 🔐 Security Considerations

### 1. Authentication
- Use strong JWT secret keys
- Implement proper user authentication
- Secure WebSocket connections

### 2. Knowledge Base Security
- Validate all knowledge inputs
- Implement content moderation
- Secure knowledge source access

### 3. API Security
- Rate limiting on RAG endpoints
- Input validation and sanitization
- Secure file storage paths

## 📈 Scaling Considerations

### Horizontal Scaling
- Use Redis for session storage
- Implement load balancing for WebSocket connections
- Scale knowledge sources independently

### Database Scaling
- Use PostgreSQL for production
- Implement read replicas
- Consider database sharding for large knowledge bases

### Vector Store Scaling
- Migrate to FAISS for large datasets
- Implement distributed vector search
- Use GPU acceleration for embeddings

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 5000

CMD ["python3", "src/main_rag_integrated.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pokerpy-rag-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pokerpy-rag-backend
  template:
    metadata:
      labels:
        app: pokerpy-rag-backend
    spec:
      containers:
      - name: backend
        image: pokerpy-rag-backend:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@postgres:5432/pokerpy"
```

## 📝 API Documentation

### RAG Search API
```
POST /api/rag/search
Content-Type: application/json

{
  "query": "string",
  "context": {
    "skill_level": "beginner|intermediate|advanced",
    "document_types": ["strategy", "hand_analysis", "concept"]
  },
  "max_results": 5
}

Response:
{
  "success": true,
  "results": {
    "documents": [...],
    "total_found": 10,
    "search_time": 0.05
  }
}
```

### Enhanced Coaching API
```
POST /api/agents/coach
Content-Type: application/json

{
  "message_type": "coaching_request",
  "content": {
    "query": "How do I improve my preflop play?",
    "user_id": "user123",
    "context": {
      "skill_level": "intermediate",
      "session_history": [...]
    }
  }
}

Response:
{
  "success": true,
  "response": "Enhanced coaching response with knowledge backing...",
  "sources": [...],
  "confidence": 0.85,
  "follow_up_suggestions": [...]
}
```

## 🎯 Next Steps

1. **Monitor Performance**: Track RAG system metrics and optimize as needed
2. **Expand Knowledge Base**: Add more poker content sources
3. **Enhance Embeddings**: Consider upgrading to transformer-based embeddings
4. **Implement Caching**: Add Redis caching for frequently accessed knowledge
5. **Add Analytics**: Implement detailed usage analytics and A/B testing

## 📞 Support

For technical support or questions about the RAG implementation:
- Check the logs for detailed error messages
- Use the health check endpoints to diagnose issues
- Monitor RAG system statistics for performance insights
- Review the troubleshooting section for common solutions

The RAG-enhanced PokerPy backend provides intelligent, knowledge-backed poker coaching that scales with your user base and continuously improves through automated knowledge ingestion.

