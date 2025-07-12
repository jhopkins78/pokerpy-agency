# PokerPy Enhanced - Intelligent Poker Coaching Agent

A comprehensive poker coaching platform featuring a psychologically intelligent AI agent with retrieval-augmented generation (RAG), goal tracking, simulation scenarios, and mental performance support.

## Features

### 🧠 Intelligent Coaching Agent
- **Psychological Profiling**: Builds detailed psychological profiles through natural conversation
- **Adaptive Communication**: Adjusts coaching style based on user preferences and emotional state
- **RAG-Powered Knowledge**: Retrieves relevant information from comprehensive poker knowledge base
- **Personalized Insights**: Provides tailored advice for both poker and life improvement

### 🎯 Goal Tracking System
- **Multi-Category Goals**: Track poker skills, mental game, financial, personal, and health goals
- **Smart Milestones**: Automatic milestone generation with personalized rewards
- **Progress Analytics**: Comprehensive analytics and trend tracking
- **Habit Engine**: Simulates behaviors of successful players

### 🎮 Simulation Room
- **Interactive Scenarios**: Practice common poker situations with real-time feedback
- **Difficulty Levels**: Beginner, intermediate, and advanced scenarios
- **Learning Objectives**: Each scenario focuses on specific skills
- **Performance Tracking**: Detailed analysis of decision-making quality

### 💭 Ask Anything Mode
- **Life Coaching**: Get advice on mental health, relationships, career, and personal development
- **Poker Metaphors**: Connect poker principles to life lessons
- **Holistic Support**: Beyond poker - spiritual, emotional, and personal growth guidance

### 📊 Memory & Analytics
- **Persistent Memory**: Remembers user preferences, history, and psychological insights
- **Session Tracking**: Comprehensive poker session analysis
- **Habit Monitoring**: Track daily, weekly, and monthly habits
- **Progress Visualization**: Visual representation of improvement over time

## Architecture

### Backend Components
- **Flask API**: RESTful API with CORS support
- **Coaching Agent**: Core AI agent with OpenAI GPT-4 integration
- **RAG System**: Vector-based knowledge retrieval with embeddings
- **Simulation Engine**: Interactive poker scenario generator
- **Goal Tracker**: Comprehensive goal and habit management
- **Memory Manager**: User data persistence and caching

### Knowledge Base
- **Poker Strategy**: Core concepts, advanced techniques, game theory
- **Psychology**: Mental game, tilt control, emotional regulation
- **Mathematics**: Probability, pot odds, expected value
- **Personal Development**: Life skills, discipline, growth mindset

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Node.js 16+ (for frontend)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export SECRET_KEY="your-secret-key"

# Run the application
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## API Endpoints

### Core Endpoints
- `POST /api/chat` - Main coaching conversation
- `GET /api/health` - Health check
- `GET /api/daily-insight` - Daily motivational insight
- `POST /api/ask-anything` - Life advice mode

### Simulation Endpoints
- `POST /api/simulation/start` - Start new simulation
- `POST /api/simulation/{id}/action` - Process simulation action
- `GET /api/simulation/{id}/history` - Get simulation history

### Goal Management
- `GET /api/goals` - Get user goals
- `POST /api/goals` - Create new goal
- `PUT /api/goals/{id}/update` - Update goal progress

### User Management
- `GET /api/profile` - Get user profile
- `POST /api/profile` - Update user profile
- `POST /api/knowledge/search` - Search knowledge base

## Usage Examples

### Starting a Coaching Conversation
```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    message: 'I keep tilting after bad beats. How can I improve my mental game?',
    context: { emotional_state: 'frustrated' }
  })
});
```

### Creating a Goal
```javascript
const goal = await fetch('/api/goals', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    goal: {
      title: 'Eliminate Tilt',
      description: 'Develop emotional control and maintain decision quality under pressure',
      category: 'mental',
      target_value: 100,
      unit: 'percentage',
      target_date: '2024-12-31'
    }
  })
});
```

### Starting a Simulation
```javascript
const simulation = await fetch('/api/simulation/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    scenario_type: 'bluff_spot',
    difficulty: 'intermediate'
  })
});
```

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
SECRET_KEY=your-flask-secret-key
DATABASE_URL=your-database-url (optional)
REDIS_URL=your-redis-url (optional)
```

### Coaching Styles
- **Supportive**: Encouraging, empathetic, confidence-building
- **Analytical**: Data-driven, logical, technical improvement
- **Motivational**: High-energy, inspiring, mindset-focused
- **Philosophical**: Deep, reflective, life lessons
- **Practical**: Direct, actionable, immediate improvements

## Knowledge Base Categories

### Poker Strategy
- Position play and hand selection
- Betting patterns and sizing
- Bluffing and value betting
- Tournament vs cash game strategy

### Psychology
- Tilt recognition and control
- Confidence building
- Decision-making under pressure
- Emotional regulation techniques

### Mathematics
- Pot odds and implied odds
- Expected value calculations
- Variance and bankroll management
- Probability and combinatorics

### Personal Development
- Discipline and habit formation
- Goal setting and achievement
- Time management
- Stress management

## Testing

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd frontend
npm test
```

## Deployment

### Production Setup
1. Set up production database (PostgreSQL recommended)
2. Configure Redis for caching and session management
3. Set up proper environment variables
4. Use Gunicorn for production WSGI server
5. Configure reverse proxy (Nginx recommended)

### Docker Deployment
```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API examples

## Roadmap

### Upcoming Features
- **Voice Integration**: Speech-to-text and text-to-speech
- **Video Analysis**: Hand history review with AI insights
- **Community Features**: Connect with other players
- **Advanced Analytics**: Machine learning-powered insights
- **Mobile App**: Native iOS and Android applications
- **Tournament Tracking**: Live tournament coaching
- **Bankroll Integration**: Real-time bankroll management

### Technical Improvements
- **Database Migration**: Move from file-based to PostgreSQL
- **Real-time Features**: WebSocket integration
- **Performance Optimization**: Caching and query optimization
- **Security Enhancements**: Advanced authentication and authorization
- **Monitoring**: Comprehensive logging and metrics
- **Scalability**: Microservices architecture

## Architecture Decisions

### Why RAG?
- Provides grounded, factual responses
- Allows for easy knowledge base updates
- Reduces hallucination in AI responses
- Enables personalized content retrieval

### Why Flask?
- Lightweight and flexible
- Easy integration with AI/ML libraries
- Excellent for rapid prototyping
- Strong ecosystem support

### Why File-based Storage Initially?
- Simplifies deployment and setup
- No external dependencies
- Easy to backup and migrate
- Suitable for MVP and testing

## Performance Considerations

- **Caching**: In-memory caching for frequently accessed data
- **Async Processing**: Background tasks for heavy computations
- **Rate Limiting**: API rate limiting to prevent abuse
- **Optimization**: Database query optimization and indexing
- **CDN**: Static asset delivery via CDN

## Security Features

- **Input Validation**: Comprehensive input sanitization
- **Authentication**: Secure user authentication
- **Data Encryption**: Sensitive data encryption at rest
- **CORS**: Proper CORS configuration
- **Rate Limiting**: Protection against abuse
- **Logging**: Security event logging and monitoring

