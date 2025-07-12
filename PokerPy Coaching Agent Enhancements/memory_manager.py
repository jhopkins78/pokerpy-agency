import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    user_id: str
    name: str
    email: str
    skill_level: str  # 'beginner', 'intermediate', 'advanced', 'expert'
    preferred_games: List[str]
    goals: List[str]
    psychological_profile: Dict
    session_history: List[Dict]
    preferences: Dict
    created_date: datetime
    last_active: datetime
    coaching_style_preference: str
    timezone: str

class MemoryManager:
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "profiles").mkdir(exist_ok=True)
        (self.data_dir / "conversations").mkdir(exist_ok=True)
        (self.data_dir / "goals").mkdir(exist_ok=True)
        (self.data_dir / "habits").mkdir(exist_ok=True)
        (self.data_dir / "sessions").mkdir(exist_ok=True)
        
        # In-memory caches for performance
        self.profile_cache = {}
        self.conversation_cache = {}
        self.goal_cache = {}
        
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID"""
        try:
            # Check cache first
            if user_id in self.profile_cache:
                return self.profile_cache[user_id]
            
            # Load from file
            profile_file = self.data_dir / "profiles" / f"{user_id}.json"
            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                
                # Convert date strings back to datetime objects
                if 'created_date' in profile_data:
                    profile_data['created_date'] = datetime.fromisoformat(profile_data['created_date'])
                if 'last_active' in profile_data:
                    profile_data['last_active'] = datetime.fromisoformat(profile_data['last_active'])
                
                # Cache and return
                self.profile_cache[user_id] = profile_data
                return profile_data
            
            # Create new profile if doesn't exist
            return self._create_default_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return self._create_default_profile(user_id)
    
    def _create_default_profile(self, user_id: str) -> Dict:
        """Create a default user profile"""
        profile = {
            "user_id": user_id,
            "name": f"User_{user_id[:8]}",
            "email": "",
            "skill_level": "beginner",
            "preferred_games": ["texas_holdem"],
            "goals": [],
            "psychological_profile": {
                "risk_tolerance": "unknown",
                "emotional_regulation": "unknown",
                "learning_style": "unknown",
                "motivation_type": "unknown",
                "communication_preference": "supportive"
            },
            "session_history": [],
            "preferences": {
                "coaching_style": "supportive",
                "notification_frequency": "daily",
                "privacy_level": "standard",
                "language": "english"
            },
            "created_date": datetime.now(),
            "last_active": datetime.now(),
            "coaching_style_preference": "supportive",
            "timezone": "UTC"
        }
        
        # Save the new profile
        self.save_user_profile(user_id, profile)
        return profile
    
    def save_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Save user profile to storage"""
        try:
            # Update last active
            profile_data['last_active'] = datetime.now()
            
            # Prepare data for JSON serialization
            serializable_data = profile_data.copy()
            if 'created_date' in serializable_data and isinstance(serializable_data['created_date'], datetime):
                serializable_data['created_date'] = serializable_data['created_date'].isoformat()
            if 'last_active' in serializable_data and isinstance(serializable_data['last_active'], datetime):
                serializable_data['last_active'] = serializable_data['last_active'].isoformat()
            
            # Save to file
            profile_file = self.data_dir / "profiles" / f"{user_id}.json"
            with open(profile_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            # Update cache
            self.profile_cache[user_id] = profile_data
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            return False
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Dict:
        """Update specific fields in user profile"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                profile = self._create_default_profile(user_id)
            
            # Apply updates
            for key, value in updates.items():
                if key in profile:
                    profile[key] = value
            
            # Save updated profile
            self.save_user_profile(user_id, profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return {}
    
    def update_psychological_profile(self, user_id: str, insights: Dict) -> bool:
        """Update psychological profile with new insights"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            # Update psychological profile
            if 'psychological_profile' not in profile:
                profile['psychological_profile'] = {}
            
            profile['psychological_profile'].update(insights)
            
            # Save updated profile
            return self.save_user_profile(user_id, profile)
            
        except Exception as e:
            logger.error(f"Error updating psychological profile: {str(e)}")
            return False
    
    def save_conversation(self, chat_message) -> bool:
        """Save a conversation message"""
        try:
            user_id = chat_message.user_id
            
            # Prepare conversation data
            conversation_data = {
                "id": chat_message.id,
                "user_id": user_id,
                "message": chat_message.message,
                "response": chat_message.response,
                "timestamp": chat_message.timestamp.isoformat(),
                "context": chat_message.context
            }
            
            # Load existing conversations for user
            conversations_file = self.data_dir / "conversations" / f"{user_id}.json"
            conversations = []
            
            if conversations_file.exists():
                with open(conversations_file, 'r') as f:
                    conversations = json.load(f)
            
            # Add new conversation
            conversations.append(conversation_data)
            
            # Keep only last 100 conversations to manage file size
            conversations = conversations[-100:]
            
            # Save back to file
            with open(conversations_file, 'w') as f:
                json.dump(conversations, f, indent=2)
            
            # Update cache
            self.conversation_cache[user_id] = conversations
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return False
    
    def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        try:
            # Check cache first
            if user_id in self.conversation_cache:
                conversations = self.conversation_cache[user_id]
            else:
                # Load from file
                conversations_file = self.data_dir / "conversations" / f"{user_id}.json"
                if conversations_file.exists():
                    with open(conversations_file, 'r') as f:
                        conversations = json.load(f)
                    self.conversation_cache[user_id] = conversations
                else:
                    conversations = []
            
            # Return most recent conversations
            return conversations[-limit:] if conversations else []
            
        except Exception as e:
            logger.error(f"Error getting recent conversations: {str(e)}")
            return []
    
    def save_goal(self, goal) -> bool:
        """Save a goal to storage"""
        try:
            user_id = goal.user_id
            
            # Prepare goal data for serialization
            goal_data = asdict(goal)
            
            # Convert datetime objects to ISO strings
            if 'created_date' in goal_data and isinstance(goal_data['created_date'], datetime):
                goal_data['created_date'] = goal_data['created_date'].isoformat()
            if 'target_date' in goal_data and goal_data['target_date'] and isinstance(goal_data['target_date'], datetime):
                goal_data['target_date'] = goal_data['target_date'].isoformat()
            
            # Load existing goals for user
            goals_file = self.data_dir / "goals" / f"{user_id}.json"
            goals = []
            
            if goals_file.exists():
                with open(goals_file, 'r') as f:
                    goals = json.load(f)
            
            # Update existing goal or add new one
            goal_updated = False
            for i, existing_goal in enumerate(goals):
                if existing_goal['id'] == goal.id:
                    goals[i] = goal_data
                    goal_updated = True
                    break
            
            if not goal_updated:
                goals.append(goal_data)
            
            # Save back to file
            with open(goals_file, 'w') as f:
                json.dump(goals, f, indent=2)
            
            # Update cache
            if user_id not in self.goal_cache:
                self.goal_cache[user_id] = []
            
            # Update cache
            goal_updated_in_cache = False
            for i, cached_goal in enumerate(self.goal_cache[user_id]):
                if cached_goal.id == goal.id:
                    self.goal_cache[user_id][i] = goal
                    goal_updated_in_cache = True
                    break
            
            if not goal_updated_in_cache:
                self.goal_cache[user_id].append(goal)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving goal: {str(e)}")
            return False
    
    def get_goal(self, goal_id: str) -> Optional[Any]:
        """Get a specific goal by ID"""
        try:
            # Search through all user goal files
            goals_dir = self.data_dir / "goals"
            for goals_file in goals_dir.glob("*.json"):
                with open(goals_file, 'r') as f:
                    goals = json.load(f)
                
                for goal_data in goals:
                    if goal_data['id'] == goal_id:
                        # Convert back to Goal object
                        from goal_tracker import Goal
                        
                        # Convert date strings back to datetime objects
                        if 'created_date' in goal_data:
                            goal_data['created_date'] = datetime.fromisoformat(goal_data['created_date'])
                        if 'target_date' in goal_data and goal_data['target_date']:
                            goal_data['target_date'] = datetime.fromisoformat(goal_data['target_date'])
                        
                        return Goal(**goal_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting goal: {str(e)}")
            return None
    
    def get_user_goals(self, user_id: str) -> List[Any]:
        """Get all goals for a user"""
        try:
            # Check cache first
            if user_id in self.goal_cache:
                return self.goal_cache[user_id]
            
            # Load from file
            goals_file = self.data_dir / "goals" / f"{user_id}.json"
            if not goals_file.exists():
                return []
            
            with open(goals_file, 'r') as f:
                goals_data = json.load(f)
            
            # Convert to Goal objects
            from goal_tracker import Goal
            goals = []
            
            for goal_data in goals_data:
                # Convert date strings back to datetime objects
                if 'created_date' in goal_data:
                    goal_data['created_date'] = datetime.fromisoformat(goal_data['created_date'])
                if 'target_date' in goal_data and goal_data['target_date']:
                    goal_data['target_date'] = datetime.fromisoformat(goal_data['target_date'])
                
                goals.append(Goal(**goal_data))
            
            # Cache and return
            self.goal_cache[user_id] = goals
            return goals
            
        except Exception as e:
            logger.error(f"Error getting user goals: {str(e)}")
            return []
    
    def save_habit_completion(self, habit_entry: Dict) -> bool:
        """Save habit completion data"""
        try:
            user_id = habit_entry['user_id']
            
            # Load existing habit data for user
            habits_file = self.data_dir / "habits" / f"{user_id}.json"
            habits = []
            
            if habits_file.exists():
                with open(habits_file, 'r') as f:
                    habits = json.load(f)
            
            # Add new habit entry
            habits.append(habit_entry)
            
            # Keep only last 1000 entries to manage file size
            habits = habits[-1000:]
            
            # Save back to file
            with open(habits_file, 'w') as f:
                json.dump(habits, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving habit completion: {str(e)}")
            return False
    
    def get_habit_completions(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get habit completions for the last N days"""
        try:
            habits_file = self.data_dir / "habits" / f"{user_id}.json"
            if not habits_file.exists():
                return []
            
            with open(habits_file, 'r') as f:
                habits = json.load(f)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_habits = []
            
            for habit in habits:
                habit_date = datetime.fromisoformat(habit['date'])
                if habit_date >= cutoff_date:
                    recent_habits.append(habit)
            
            return recent_habits
            
        except Exception as e:
            logger.error(f"Error getting habit completions: {str(e)}")
            return []
    
    def save_session_data(self, user_id: str, session_data: Dict) -> bool:
        """Save poker session data"""
        try:
            # Load existing sessions for user
            sessions_file = self.data_dir / "sessions" / f"{user_id}.json"
            sessions = []
            
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
            
            # Add new session
            session_data['timestamp'] = datetime.now().isoformat()
            sessions.append(session_data)
            
            # Keep only last 500 sessions to manage file size
            sessions = sessions[-500:]
            
            # Save back to file
            with open(sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving session data: {str(e)}")
            return False
    
    def get_session_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get recent session history"""
        try:
            sessions_file = self.data_dir / "sessions" / f"{user_id}.json"
            if not sessions_file.exists():
                return []
            
            with open(sessions_file, 'r') as f:
                sessions = json.load(f)
            
            return sessions[-limit:] if sessions else []
            
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            return []
    
    def get_user_statistics(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        try:
            profile = self.get_user_profile(user_id)
            goals = self.get_user_goals(user_id)
            conversations = self.get_recent_conversations(user_id, limit=100)
            sessions = self.get_session_history(user_id)
            habits = self.get_habit_completions(user_id, days=30)
            
            stats = {
                "profile": {
                    "skill_level": profile.get('skill_level', 'unknown'),
                    "days_active": (datetime.now() - datetime.fromisoformat(profile.get('created_date', datetime.now().isoformat()))).days,
                    "last_active": profile.get('last_active', 'unknown')
                },
                "goals": {
                    "total": len(goals),
                    "active": len([g for g in goals if g.status == 'active']),
                    "completed": len([g for g in goals if g.status == 'completed'])
                },
                "engagement": {
                    "total_conversations": len(conversations),
                    "sessions_tracked": len(sessions),
                    "habits_completed": len([h for h in habits if h['completed']])
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> bool:
        """Clean up old data to manage storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # This would implement cleanup logic for old conversations, habits, etc.
            # For now, just log the action
            logger.info(f"Cleanup requested for data older than {cutoff_date}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return False

