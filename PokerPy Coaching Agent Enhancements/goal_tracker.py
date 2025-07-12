import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Goal:
    id: str
    user_id: str
    title: str
    description: str
    category: str  # 'poker', 'mental', 'financial', 'personal', 'health'
    target_value: Optional[float]
    current_value: float
    unit: str  # 'hours', 'sessions', 'dollars', 'percentage', 'count'
    target_date: Optional[datetime]
    created_date: datetime
    status: str  # 'active', 'completed', 'paused', 'cancelled'
    priority: str  # 'low', 'medium', 'high', 'critical'
    milestones: List[Dict]
    progress_history: List[Dict]
    habits: List[str]
    success_criteria: Dict
    
class GoalTracker:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.goal_categories = {
            "poker": {
                "name": "Poker Skills",
                "description": "Technical poker improvement goals",
                "common_goals": [
                    "Improve win rate",
                    "Move up stakes",
                    "Master tournament play",
                    "Reduce variance",
                    "Learn new format"
                ]
            },
            "mental": {
                "name": "Mental Game",
                "description": "Psychological and emotional development",
                "common_goals": [
                    "Eliminate tilt",
                    "Improve focus",
                    "Build confidence",
                    "Develop patience",
                    "Enhance decision-making"
                ]
            },
            "financial": {
                "name": "Bankroll & Finance",
                "description": "Financial management and growth",
                "common_goals": [
                    "Build bankroll",
                    "Improve ROI",
                    "Stick to bankroll management",
                    "Diversify income",
                    "Track expenses"
                ]
            },
            "personal": {
                "name": "Personal Development",
                "description": "Life skills and personal growth",
                "common_goals": [
                    "Develop discipline",
                    "Improve time management",
                    "Build relationships",
                    "Learn new skills",
                    "Achieve work-life balance"
                ]
            },
            "health": {
                "name": "Health & Wellness",
                "description": "Physical and mental health",
                "common_goals": [
                    "Exercise regularly",
                    "Improve sleep",
                    "Manage stress",
                    "Eat healthier",
                    "Practice mindfulness"
                ]
            }
        }
        
        # Habit templates for successful players
        self.success_habits = {
            "daily": [
                "Review previous session hands",
                "Study poker theory for 30 minutes",
                "Practice mindfulness/meditation",
                "Exercise for 30 minutes",
                "Track session results",
                "Set daily intentions",
                "Reflect on decisions made"
            ],
            "weekly": [
                "Analyze weekly performance",
                "Review and update goals",
                "Study advanced concepts",
                "Network with other players",
                "Take a complete rest day",
                "Plan upcoming sessions",
                "Review bankroll status"
            ],
            "monthly": [
                "Comprehensive game review",
                "Update strategy based on results",
                "Set new learning objectives",
                "Evaluate goal progress",
                "Seek coaching or feedback",
                "Analyze long-term trends",
                "Celebrate achievements"
            ]
        }
    
    def create_goal(self, user_id: str, goal_data: Dict) -> Dict:
        """Create a new goal for the user"""
        try:
            goal_id = str(uuid.uuid4())
            
            # Validate required fields
            required_fields = ['title', 'description', 'category']
            for field in required_fields:
                if field not in goal_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Parse target date if provided
            target_date = None
            if 'target_date' in goal_data and goal_data['target_date']:
                if isinstance(goal_data['target_date'], str):
                    target_date = datetime.fromisoformat(goal_data['target_date'].replace('Z', '+00:00'))
                else:
                    target_date = goal_data['target_date']
            
            # Create goal object
            goal = Goal(
                id=goal_id,
                user_id=user_id,
                title=goal_data['title'],
                description=goal_data['description'],
                category=goal_data['category'],
                target_value=goal_data.get('target_value'),
                current_value=goal_data.get('current_value', 0.0),
                unit=goal_data.get('unit', 'count'),
                target_date=target_date,
                created_date=datetime.now(),
                status='active',
                priority=goal_data.get('priority', 'medium'),
                milestones=goal_data.get('milestones', []),
                progress_history=[],
                habits=goal_data.get('habits', []),
                success_criteria=goal_data.get('success_criteria', {})
            )
            
            # Generate automatic milestones if target value is provided
            if goal.target_value and not goal.milestones:
                goal.milestones = self._generate_milestones(goal)
            
            # Suggest relevant habits
            if not goal.habits:
                goal.habits = self._suggest_habits(goal)
            
            # Save goal
            self.memory_manager.save_goal(goal)
            
            return asdict(goal)
            
        except Exception as e:
            logger.error(f"Error creating goal: {str(e)}")
            raise
    
    def _generate_milestones(self, goal: Goal) -> List[Dict]:
        """Generate automatic milestones for a goal"""
        milestones = []
        
        if goal.target_value:
            # Create milestones at 25%, 50%, 75%, and 100%
            percentages = [0.25, 0.5, 0.75, 1.0]
            
            for i, pct in enumerate(percentages):
                milestone_value = goal.target_value * pct
                milestone = {
                    "id": str(uuid.uuid4()),
                    "title": f"{int(pct * 100)}% Progress",
                    "description": f"Reach {milestone_value} {goal.unit}",
                    "target_value": milestone_value,
                    "completed": False,
                    "completed_date": None,
                    "reward": self._suggest_milestone_reward(goal.category, pct)
                }
                milestones.append(milestone)
        
        return milestones
    
    def _suggest_milestone_reward(self, category: str, percentage: float) -> str:
        """Suggest a reward for reaching a milestone"""
        rewards = {
            "poker": {
                0.25: "Review a training video",
                0.5: "Play a fun tournament",
                0.75: "Buy a poker book",
                1.0: "Celebrate with a special session"
            },
            "mental": {
                0.25: "Take a relaxing break",
                0.5: "Try a new meditation technique",
                0.75: "Share progress with a friend",
                1.0: "Treat yourself to something special"
            },
            "financial": {
                0.25: "Track your progress visually",
                0.5: "Review and optimize strategy",
                0.75: "Consider moving up stakes",
                1.0: "Celebrate financial milestone"
            },
            "personal": {
                0.25: "Acknowledge your progress",
                0.5: "Share achievement with others",
                0.75: "Take on a new challenge",
                1.0: "Celebrate personal growth"
            },
            "health": {
                0.25: "Try a new healthy recipe",
                0.5: "Buy new workout gear",
                0.75: "Plan a healthy activity",
                1.0: "Celebrate improved health"
            }
        }
        
        return rewards.get(category, {}).get(percentage, "Celebrate your progress!")
    
    def _suggest_habits(self, goal: Goal) -> List[str]:
        """Suggest relevant habits for a goal"""
        habit_suggestions = {
            "poker": [
                "Study poker theory daily",
                "Review session hands",
                "Track session results",
                "Practice bankroll management"
            ],
            "mental": [
                "Practice mindfulness meditation",
                "Keep a decision journal",
                "Use breathing exercises",
                "Practice positive self-talk"
            ],
            "financial": [
                "Track all poker expenses",
                "Review bankroll weekly",
                "Set session stop-losses",
                "Calculate hourly rates"
            ],
            "personal": [
                "Set daily intentions",
                "Reflect on daily progress",
                "Practice gratitude",
                "Maintain work-life balance"
            ],
            "health": [
                "Exercise regularly",
                "Maintain sleep schedule",
                "Eat nutritious meals",
                "Take regular breaks"
            ]
        }
        
        return habit_suggestions.get(goal.category, ["Track daily progress"])
    
    def update_progress(self, goal_id: str, progress: float, notes: str = "") -> Dict:
        """Update progress on a goal"""
        try:
            goal = self.memory_manager.get_goal(goal_id)
            if not goal:
                raise ValueError("Goal not found")
            
            # Record progress history
            progress_entry = {
                "date": datetime.now().isoformat(),
                "previous_value": goal.current_value,
                "new_value": progress,
                "change": progress - goal.current_value,
                "notes": notes
            }
            
            goal.progress_history.append(progress_entry)
            goal.current_value = progress
            
            # Check for milestone completions
            self._check_milestones(goal)
            
            # Check if goal is completed
            if goal.target_value and progress >= goal.target_value:
                goal.status = 'completed'
                self._celebrate_goal_completion(goal)
            
            # Save updated goal
            self.memory_manager.save_goal(goal)
            
            return asdict(goal)
            
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            raise
    
    def _check_milestones(self, goal: Goal):
        """Check and mark completed milestones"""
        for milestone in goal.milestones:
            if not milestone["completed"] and goal.current_value >= milestone["target_value"]:
                milestone["completed"] = True
                milestone["completed_date"] = datetime.now().isoformat()
    
    def _celebrate_goal_completion(self, goal: Goal):
        """Handle goal completion celebration"""
        # This could trigger notifications, rewards, etc.
        logger.info(f"Goal completed: {goal.title} for user {goal.user_id}")
    
    def get_user_goals(self, user_id: str, status: str = None, category: str = None) -> List[Dict]:
        """Get all goals for a user with optional filtering"""
        try:
            goals = self.memory_manager.get_user_goals(user_id)
            
            # Apply filters
            if status:
                goals = [g for g in goals if g.status == status]
            
            if category:
                goals = [g for g in goals if g.category == category]
            
            # Sort by priority and creation date
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            goals.sort(key=lambda g: (priority_order.get(g.priority, 2), g.created_date), reverse=True)
            
            return [asdict(goal) for goal in goals]
            
        except Exception as e:
            logger.error(f"Error getting user goals: {str(e)}")
            return []
    
    def get_goal_analytics(self, user_id: str, timeframe: str = "month") -> Dict:
        """Get analytics for user's goals"""
        try:
            goals = self.memory_manager.get_user_goals(user_id)
            
            # Calculate timeframe
            now = datetime.now()
            if timeframe == "week":
                start_date = now - timedelta(weeks=1)
            elif timeframe == "month":
                start_date = now - timedelta(days=30)
            elif timeframe == "quarter":
                start_date = now - timedelta(days=90)
            else:
                start_date = now - timedelta(days=365)
            
            analytics = {
                "total_goals": len(goals),
                "active_goals": len([g for g in goals if g.status == 'active']),
                "completed_goals": len([g for g in goals if g.status == 'completed']),
                "completion_rate": 0,
                "categories": {},
                "progress_trend": [],
                "milestones_completed": 0,
                "habits_tracked": 0
            }
            
            # Calculate completion rate
            if analytics["total_goals"] > 0:
                analytics["completion_rate"] = analytics["completed_goals"] / analytics["total_goals"]
            
            # Category breakdown
            for goal in goals:
                if goal.category not in analytics["categories"]:
                    analytics["categories"][goal.category] = {
                        "total": 0,
                        "completed": 0,
                        "active": 0
                    }
                
                analytics["categories"][goal.category]["total"] += 1
                if goal.status == 'completed':
                    analytics["categories"][goal.category]["completed"] += 1
                elif goal.status == 'active':
                    analytics["categories"][goal.category]["active"] += 1
            
            # Count milestones and habits
            for goal in goals:
                analytics["milestones_completed"] += len([m for m in goal.milestones if m["completed"]])
                analytics["habits_tracked"] += len(goal.habits)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting goal analytics: {str(e)}")
            return {}
    
    def suggest_new_goals(self, user_id: str) -> List[Dict]:
        """Suggest new goals based on user profile and current goals"""
        try:
            user_profile = self.memory_manager.get_user_profile(user_id)
            current_goals = self.memory_manager.get_user_goals(user_id)
            
            suggestions = []
            
            # Analyze current goal categories
            current_categories = set(goal.category for goal in current_goals if goal.status == 'active')
            
            # Suggest goals for missing categories
            for category, info in self.goal_categories.items():
                if category not in current_categories:
                    for common_goal in info["common_goals"][:2]:  # Suggest top 2
                        suggestion = {
                            "title": common_goal,
                            "category": category,
                            "description": f"Improve your {info['name'].lower()}",
                            "priority": "medium",
                            "suggested_habits": self._suggest_habits(type('Goal', (), {'category': category})())
                        }
                        suggestions.append(suggestion)
            
            # Personalized suggestions based on user profile
            if user_profile:
                psychological_profile = user_profile.get('psychological_profile', {})
                
                if psychological_profile.get('risk_tolerance') == 'low':
                    suggestions.append({
                        "title": "Build confidence in decision-making",
                        "category": "mental",
                        "description": "Develop comfort with calculated risks",
                        "priority": "high"
                    })
                
                if psychological_profile.get('emotional_regulation') == 'needs_work':
                    suggestions.append({
                        "title": "Master emotional control",
                        "category": "mental",
                        "description": "Eliminate tilt and improve decision quality",
                        "priority": "critical"
                    })
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting goals: {str(e)}")
            return []
    
    def get_habit_engine_data(self, user_id: str) -> Dict:
        """Get habit data for the habit engine"""
        try:
            goals = self.memory_manager.get_user_goals(user_id)
            
            # Collect all habits from active goals
            all_habits = []
            for goal in goals:
                if goal.status == 'active':
                    all_habits.extend(goal.habits)
            
            # Add success habits based on user level
            user_profile = self.memory_manager.get_user_profile(user_id)
            skill_level = user_profile.get('skill_level', 'beginner') if user_profile else 'beginner'
            
            recommended_habits = {
                "daily": self.success_habits["daily"][:3],  # Top 3 daily habits
                "weekly": self.success_habits["weekly"][:2],  # Top 2 weekly habits
                "monthly": self.success_habits["monthly"][:1]  # Top 1 monthly habit
            }
            
            return {
                "user_habits": list(set(all_habits)),  # Remove duplicates
                "recommended_habits": recommended_habits,
                "success_habits": self.success_habits,
                "habit_categories": list(self.goal_categories.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting habit engine data: {str(e)}")
            return {}
    
    def track_habit_completion(self, user_id: str, habit: str, completed: bool, date: datetime = None) -> bool:
        """Track completion of a habit"""
        try:
            if not date:
                date = datetime.now()
            
            habit_entry = {
                "habit": habit,
                "completed": completed,
                "date": date.isoformat(),
                "user_id": user_id
            }
            
            # Save habit completion (this would typically go to a separate habits table)
            self.memory_manager.save_habit_completion(habit_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking habit completion: {str(e)}")
            return False
    
    def get_categories(self) -> Dict:
        """Get available goal categories"""
        return self.goal_categories

