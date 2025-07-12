# Lovable Frontend Update Prompt for PokerPy Enhanced

## Project Overview
Update the existing PokerPy frontend to integrate with the new Enhanced PokerPy backend that includes an intelligent poker coaching agent with psychological profiling, goal tracking, simulation scenarios, and comprehensive mental performance support.

## New Features to Implement

### 1. Intelligent Coaching Chat Interface
Create a sophisticated chat interface for the AI coaching agent:

**Components Needed:**
- `CoachingChat.tsx` - Main chat component with message history
- `MessageBubble.tsx` - Individual message display with coaching/user distinction
- `TypingIndicator.tsx` - Shows when coach is "thinking"
- `SuggestionChips.tsx` - Quick action buttons for common questions
- `EmotionalStateSelector.tsx` - Allow users to indicate current emotional state

**Features:**
- Real-time chat with the coaching agent
- Message history with timestamps
- Emotional tone indicators (supportive, analytical, motivational, etc.)
- Quick suggestion buttons for common coaching topics
- Ability to set context (recent session results, emotional state)
- Daily insight notifications

**API Integration:**
```typescript
// Chat endpoint
POST /api/chat
{
  user_id: string,
  message: string,
  context: {
    emotional_state?: string,
    recent_performance?: string,
    session_type?: string
  }
}

// Daily insight endpoint
GET /api/daily-insight?user_id={userId}
```

### 2. Goal Tracking Dashboard
Implement a comprehensive goal management system:

**Components Needed:**
- `GoalsDashboard.tsx` - Main goals overview
- `GoalCard.tsx` - Individual goal display with progress
- `CreateGoalModal.tsx` - Goal creation form
- `MilestoneTracker.tsx` - Visual milestone progress
- `GoalAnalytics.tsx` - Charts and statistics
- `HabitTracker.tsx` - Daily/weekly habit tracking

**Features:**
- Create goals across categories (poker, mental, financial, personal, health)
- Visual progress tracking with milestone celebrations
- Goal analytics with charts (completion rates, trends)
- Habit tracking with streak counters
- Smart goal suggestions based on user profile
- Achievement badges and rewards

**API Integration:**
```typescript
// Goals endpoints
GET /api/goals?user_id={userId}&category={category}
POST /api/goals
PUT /api/goals/{goalId}/update
```

### 3. Poker Simulation Room
Create an interactive poker training environment:

**Components Needed:**
- `SimulationRoom.tsx` - Main simulation interface
- `PokerTable.tsx` - Visual poker table representation
- `PlayerAvatar.tsx` - Player representations with stacks
- `ActionButtons.tsx` - Fold, call, raise, bet buttons
- `HandHistory.tsx` - Action history display
- `ScenarioSelector.tsx` - Choose simulation scenarios
- `FeedbackPanel.tsx` - Real-time coaching feedback

**Features:**
- Interactive poker scenarios (cash game, tournament, specific situations)
- Real-time decision feedback from coaching agent
- Difficulty levels (beginner, intermediate, advanced)
- Performance tracking and analysis
- Custom scenario parameters
- Learning objective tracking

**API Integration:**
```typescript
// Simulation endpoints
POST /api/simulation/start
POST /api/simulation/{simulationId}/action
GET /api/simulation/{simulationId}/history
```

### 4. Ask Anything Mode
Implement a life coaching interface:

**Components Needed:**
- `AskAnythingChat.tsx` - Dedicated life advice chat
- `CategorySelector.tsx` - Choose advice category
- `TopicSuggestions.tsx` - Common life coaching topics
- `AdviceHistory.tsx` - Previous advice sessions

**Features:**
- Life advice beyond poker (mental health, relationships, career)
- Category-based advice (personal development, spirituality, learning)
- Connection of poker principles to life lessons
- Advice history and favorites
- Anonymous mode for sensitive topics

**API Integration:**
```typescript
POST /api/ask-anything
{
  user_id: string,
  question: string,
  category: string
}
```

### 5. User Profile & Psychology Dashboard
Create a comprehensive user profile system:

**Components Needed:**
- `ProfileDashboard.tsx` - Main profile overview
- `PsychologicalProfile.tsx` - Personality insights display
- `SkillAssessment.tsx` - Poker skill evaluation
- `PreferencesSettings.tsx` - Coaching style preferences
- `SessionHistory.tsx` - Poker session tracking
- `ProgressTimeline.tsx` - Overall improvement timeline

**Features:**
- Psychological profile visualization
- Skill level assessment and tracking
- Coaching style preferences
- Session history with analytics
- Progress timeline with key milestones
- Privacy settings and data export

### 6. Knowledge Base Search
Implement searchable poker knowledge:

**Components Needed:**
- `KnowledgeSearch.tsx` - Search interface
- `SearchResults.tsx` - Results display
- `KnowledgeCard.tsx` - Individual knowledge item
- `CategoryFilter.tsx` - Filter by knowledge category

**Features:**
- Search poker strategy, psychology, mathematics
- Category filtering (strategy, mental game, probability)
- Relevance scoring and highlighting
- Bookmark favorite knowledge items
- Related content suggestions

**API Integration:**
```typescript
POST /api/knowledge/search
{
  query: string,
  category?: string,
  limit?: number
}
```

## UI/UX Design Guidelines

### Design System
- **Color Palette**: 
  - Primary: Deep blue (#1e3a8a) for trust and professionalism
  - Secondary: Green (#059669) for growth and success
  - Accent: Orange (#ea580c) for energy and motivation
  - Neutral: Gray scale for backgrounds and text
  - Success: Green for achievements and positive feedback
  - Warning: Yellow for caution and attention
  - Error: Red for mistakes and negative outcomes

### Typography
- **Headers**: Bold, clear fonts (Inter or similar)
- **Body**: Readable sans-serif (Inter or Roboto)
- **Code/Numbers**: Monospace for poker odds and calculations

### Layout Principles
- **Mobile-first**: Responsive design for all screen sizes
- **Card-based**: Use cards for distinct content sections
- **Progressive disclosure**: Show basic info first, details on demand
- **Consistent spacing**: Use 8px grid system
- **Clear hierarchy**: Distinct visual levels for information importance

### Coaching Agent Personality
- **Visual Identity**: Friendly but professional avatar
- **Tone Indicators**: Visual cues for different coaching styles
- **Emotional Intelligence**: Adapt UI based on user's emotional state
- **Encouragement**: Celebration animations for achievements

## Technical Implementation

### State Management
Use React Context or Redux Toolkit for:
- User authentication and profile
- Chat message history
- Goal tracking data
- Simulation state
- Knowledge base cache

### Real-time Features
Implement WebSocket connections for:
- Live coaching chat
- Real-time simulation updates
- Goal progress notifications
- Daily insight delivery

### Performance Optimization
- Lazy loading for heavy components
- Memoization for expensive calculations
- Virtual scrolling for long lists
- Image optimization for avatars and graphics

### Accessibility
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast mode support
- Text size adjustment options

## Integration Points

### Backend API Base URL
```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
```

### Authentication
Implement user session management:
```typescript
interface User {
  id: string;
  name: string;
  skill_level: string;
  preferences: UserPreferences;
  psychological_profile: PsychProfile;
}
```

### Error Handling
Implement comprehensive error handling:
- Network errors with retry mechanisms
- Validation errors with clear messaging
- Graceful degradation for offline scenarios
- Error boundaries for component crashes

## Testing Strategy

### Unit Tests
- Component rendering tests
- User interaction tests
- API integration tests
- State management tests

### Integration Tests
- End-to-end user flows
- Chat conversation flows
- Goal creation and tracking
- Simulation scenarios

### Performance Tests
- Load testing for chat interface
- Memory usage monitoring
- Bundle size optimization

## Deployment Considerations

### Environment Variables
```bash
REACT_APP_API_URL=https://api.pokerpy.com
REACT_APP_WS_URL=wss://ws.pokerpy.com
REACT_APP_ENVIRONMENT=production
```

### Build Optimization
- Code splitting by route
- Tree shaking for unused code
- Asset optimization and compression
- Service worker for offline functionality

## Success Metrics

### User Engagement
- Daily active users in coaching chat
- Goal completion rates
- Simulation scenario completions
- Knowledge base search usage

### User Experience
- Chat response satisfaction ratings
- Goal achievement celebrations
- Simulation learning effectiveness
- Overall app retention rates

## Implementation Priority

### Phase 1 (MVP)
1. Coaching chat interface
2. Basic goal tracking
3. User profile system
4. Knowledge base search

### Phase 2 (Enhanced)
1. Simulation room
2. Advanced goal analytics
3. Ask anything mode
4. Psychological profiling dashboard

### Phase 3 (Advanced)
1. Real-time features
2. Advanced analytics
3. Social features
4. Mobile optimization

This comprehensive update will transform PokerPy into a sophisticated poker coaching platform that combines technical poker training with psychological development and personal growth, creating a unique and valuable experience for poker players at all levels.

