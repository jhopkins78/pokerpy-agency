"""
Learning Path Agent for PokerPy
Manages personalized learning paths and progress tracking
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent, AgentMessage, AgentCapability

@dataclass
class LearningModule:
    """Represents a learning module in the curriculum"""
    id: str
    title: str
    description: str
    difficulty: str  # beginner, intermediate, advanced
    prerequisites: List[str]
    estimated_time: int  # minutes
    content_type: str  # video, article, exercise, quiz
    tags: List[str]

@dataclass
class UserProgress:
    """Tracks user progress through learning modules"""
    user_id: str
    module_id: str
    status: str  # not_started, in_progress, completed, mastered
    start_date: datetime
    completion_date: Optional[datetime]
    score: Optional[float]
    time_spent: int  # minutes
    attempts: int

class LearningPathAgent(BaseAgent):
    """
    Manages personalized learning paths and tracks user progress
    Adapts curriculum based on user performance and identified weaknesses
    """
    
    def __init__(self):
        super().__init__(
            agent_id="learning_path",
            name="Learning Path Manager",
            description="Creates personalized learning paths and tracks progress"
        )
        
        # Learning curriculum database
        self.learning_modules = self._initialize_curriculum()
        self.user_progress = {}  # user_id -> List[UserProgress]
        self.learning_paths = {}  # user_id -> personalized learning path
        self.skill_assessments = {}  # user_id -> skill assessment results
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="create_learning_path",
                description="Create personalized learning path based on user assessment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "skill_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        "identified_weaknesses": {"type": "array"},
                        "learning_goals": {"type": "array"},
                        "time_availability": {"type": "string"},
                        "preferred_learning_style": {"type": "string"}
                    },
                    "required": ["user_id", "skill_level"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "learning_path": {"type": "object"},
                        "recommended_modules": {"type": "array"},
                        "estimated_timeline": {"type": "string"}
                    }
                }
            ),
            AgentCapability(
                name="track_progress",
                description="Track and update user progress through learning modules",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "module_id": {"type": "string"},
                        "progress_data": {"type": "object"}
                    },
                    "required": ["user_id", "module_id", "progress_data"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "updated_progress": {"type": "object"},
                        "next_recommendations": {"type": "array"},
                        "achievements": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="assess_skill_level",
                description="Assess user's current skill level and knowledge gaps",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "assessment_data": {"type": "object"},
                        "hand_analysis_results": {"type": "array"}
                    },
                    "required": ["user_id", "assessment_data"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "skill_assessment": {"type": "object"},
                        "knowledge_gaps": {"type": "array"},
                        "strengths": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="recommend_next_steps",
                description="Recommend next learning steps based on current progress",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "current_context": {"type": "object"}
                    },
                    "required": ["user_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "next_modules": {"type": "array"},
                        "practice_exercises": {"type": "array"},
                        "review_topics": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process learning path management requests"""
        try:
            message_type = message.message_type
            content = message.content
            
            if message_type == "create_learning_path":
                result = await self._create_learning_path(content)
            elif message_type == "track_progress":
                result = await self._track_progress(content)
            elif message_type == "assess_skill_level":
                result = await self._assess_skill_level(content)
            elif message_type == "recommend_next_steps":
                result = await self._recommend_next_steps(content)
            else:
                result = {"error": f"Unknown message type: {message_type}"}
            
            return AgentMessage(
                id=f"response_{message.id}",
                sender=self.agent_id,
                recipient=message.sender,
                message_type=f"response_{message_type}",
                content=result,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing learning path message: {e}")
            return AgentMessage(
                id=f"error_{message.id}",
                sender=self.agent_id,
                recipient=message.sender,
                message_type="error",
                content={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _create_learning_path(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized learning path for user"""
        user_id = data.get("user_id")
        skill_level = data.get("skill_level", "beginner")
        weaknesses = data.get("identified_weaknesses", [])
        goals = data.get("learning_goals", [])
        time_availability = data.get("time_availability", "moderate")
        learning_style = data.get("preferred_learning_style", "mixed")
        
        # Create personalized learning path
        learning_path = self._build_personalized_path(
            skill_level, weaknesses, goals, time_availability, learning_style
        )
        
        # Store learning path for user
        self.learning_paths[user_id] = learning_path
        
        # Initialize progress tracking
        if user_id not in self.user_progress:
            self.user_progress[user_id] = []
        
        # Get recommended modules for immediate start
        recommended_modules = self._get_starting_modules(learning_path)
        
        # Estimate timeline
        estimated_timeline = self._estimate_completion_time(learning_path, time_availability)
        
        return {
            "learning_path": learning_path,
            "recommended_modules": recommended_modules,
            "estimated_timeline": estimated_timeline,
            "total_modules": len(learning_path["modules"]),
            "difficulty_distribution": self._analyze_difficulty_distribution(learning_path)
        }
    
    async def _track_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track user progress through learning modules"""
        user_id = data.get("user_id")
        module_id = data.get("module_id")
        progress_data = data.get("progress_data", {})
        
        # Update progress record
        progress = self._update_user_progress(user_id, module_id, progress_data)
        
        # Check for achievements
        achievements = self._check_achievements(user_id, progress)
        
        # Get next recommendations
        next_recommendations = self._get_next_recommendations(user_id)
        
        # Update learning path if needed
        self._adapt_learning_path(user_id, progress)
        
        return {
            "updated_progress": progress.__dict__ if progress else {},
            "next_recommendations": next_recommendations,
            "achievements": achievements,
            "overall_progress": self._calculate_overall_progress(user_id),
            "streak_info": self._get_learning_streak(user_id)
        }
    
    async def _assess_skill_level(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess user's current skill level"""
        user_id = data.get("user_id")
        assessment_data = data.get("assessment_data", {})
        hand_results = data.get("hand_analysis_results", [])
        
        # Analyze assessment responses
        skill_scores = self._analyze_assessment_responses(assessment_data)
        
        # Analyze hand analysis performance
        hand_performance = self._analyze_hand_performance(hand_results)
        
        # Combine assessments
        overall_assessment = self._combine_assessments(skill_scores, hand_performance)
        
        # Identify knowledge gaps and strengths
        knowledge_gaps = self._identify_knowledge_gaps(overall_assessment)
        strengths = self._identify_strengths(overall_assessment)
        
        # Store assessment results
        self.skill_assessments[user_id] = overall_assessment
        
        return {
            "skill_assessment": overall_assessment,
            "knowledge_gaps": knowledge_gaps,
            "strengths": strengths,
            "recommended_focus_areas": self._recommend_focus_areas(knowledge_gaps),
            "confidence_level": overall_assessment.get("confidence", 0.7)
        }
    
    async def _recommend_next_steps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend next learning steps"""
        user_id = data.get("user_id")
        current_context = data.get("current_context", {})
        
        # Get user's current progress and learning path
        user_progress = self.user_progress.get(user_id, [])
        learning_path = self.learning_paths.get(user_id, {})
        
        # Determine next modules
        next_modules = self._determine_next_modules(user_id, user_progress, learning_path)
        
        # Suggest practice exercises
        practice_exercises = self._suggest_practice_exercises(user_id, current_context)
        
        # Identify review topics
        review_topics = self._identify_review_topics(user_id, user_progress)
        
        return {
            "next_modules": next_modules,
            "practice_exercises": practice_exercises,
            "review_topics": review_topics,
            "study_schedule": self._create_study_schedule(user_id),
            "motivation_message": self._generate_motivation_message(user_id)
        }
    
    def _initialize_curriculum(self) -> Dict[str, LearningModule]:
        """Initialize the learning curriculum"""
        modules = {}
        
        # Beginner modules
        modules["poker_basics"] = LearningModule(
            id="poker_basics",
            title="Poker Fundamentals",
            description="Learn the basic rules and hand rankings",
            difficulty="beginner",
            prerequisites=[],
            estimated_time=30,
            content_type="video",
            tags=["fundamentals", "rules", "hand-rankings"]
        )
        
        modules["position_basics"] = LearningModule(
            id="position_basics",
            title="Understanding Position",
            description="Why position is crucial in poker",
            difficulty="beginner",
            prerequisites=["poker_basics"],
            estimated_time=25,
            content_type="video",
            tags=["position", "strategy", "fundamentals"]
        )
        
        modules["starting_hands"] = LearningModule(
            id="starting_hands",
            title="Starting Hand Selection",
            description="Which hands to play from which positions",
            difficulty="beginner",
            prerequisites=["poker_basics", "position_basics"],
            estimated_time=35,
            content_type="article",
            tags=["preflop", "hand-selection", "ranges"]
        )
        
        # Intermediate modules
        modules["pot_odds"] = LearningModule(
            id="pot_odds",
            title="Pot Odds and Equity",
            description="Understanding pot odds and hand equity",
            difficulty="intermediate",
            prerequisites=["starting_hands"],
            estimated_time=40,
            content_type="video",
            tags=["math", "equity", "pot-odds"]
        )
        
        modules["c_betting"] = LearningModule(
            id="c_betting",
            title="Continuation Betting",
            description="When and how to continuation bet",
            difficulty="intermediate",
            prerequisites=["pot_odds"],
            estimated_time=45,
            content_type="article",
            tags=["postflop", "c-bet", "aggression"]
        )
        
        # Advanced modules
        modules["range_construction"] = LearningModule(
            id="range_construction",
            title="Range Construction",
            description="Building and analyzing hand ranges",
            difficulty="advanced",
            prerequisites=["c_betting"],
            estimated_time=60,
            content_type="video",
            tags=["ranges", "advanced", "theory"]
        )
        
        return modules
    
    def _build_personalized_path(self, skill_level: str, weaknesses: List[Dict], 
                                goals: List[str], time_availability: str, 
                                learning_style: str) -> Dict[str, Any]:
        """Build personalized learning path"""
        path = {
            "user_skill_level": skill_level,
            "modules": [],
            "focus_areas": [],
            "estimated_hours": 0,
            "adaptive_features": True
        }
        
        # Start with fundamentals for beginners
        if skill_level == "beginner":
            path["modules"].extend([
                "poker_basics", "position_basics", "starting_hands", "pot_odds"
            ])
        elif skill_level == "intermediate":
            path["modules"].extend([
                "pot_odds", "c_betting", "range_construction"
            ])
        else:  # advanced
            path["modules"].extend([
                "range_construction"
            ])
        
        # Add modules based on identified weaknesses
        for weakness in weaknesses:
            weakness_type = weakness.get("leak_type", "")
            if "preflop" in weakness_type and "starting_hands" not in path["modules"]:
                path["modules"].append("starting_hands")
            elif "postflop" in weakness_type and "c_betting" not in path["modules"]:
                path["modules"].append("c_betting")
        
        # Calculate estimated time
        total_time = sum(
            self.learning_modules[module_id].estimated_time 
            for module_id in path["modules"] 
            if module_id in self.learning_modules
        )
        path["estimated_hours"] = total_time / 60
        
        return path
    
    def _get_starting_modules(self, learning_path: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommended starting modules"""
        modules = learning_path.get("modules", [])
        starting_modules = []
        
        for module_id in modules[:3]:  # First 3 modules
            if module_id in self.learning_modules:
                module = self.learning_modules[module_id]
                starting_modules.append({
                    "id": module.id,
                    "title": module.title,
                    "description": module.description,
                    "estimated_time": module.estimated_time,
                    "difficulty": module.difficulty
                })
        
        return starting_modules
    
    def _estimate_completion_time(self, learning_path: Dict[str, Any], time_availability: str) -> str:
        """Estimate completion timeline"""
        total_hours = learning_path.get("estimated_hours", 0)
        
        weekly_hours = {
            "light": 2,
            "moderate": 5,
            "intensive": 10
        }
        
        hours_per_week = weekly_hours.get(time_availability, 5)
        weeks = max(1, int(total_hours / hours_per_week))
        
        return f"{weeks} weeks"
    
    def _analyze_difficulty_distribution(self, learning_path: Dict[str, Any]) -> Dict[str, int]:
        """Analyze difficulty distribution of modules"""
        distribution = {"beginner": 0, "intermediate": 0, "advanced": 0}
        
        for module_id in learning_path.get("modules", []):
            if module_id in self.learning_modules:
                difficulty = self.learning_modules[module_id].difficulty
                distribution[difficulty] += 1
        
        return distribution
    
    def _update_user_progress(self, user_id: str, module_id: str, 
                            progress_data: Dict[str, Any]) -> Optional[UserProgress]:
        """Update user progress for a module"""
        # Find existing progress record
        user_progress_list = self.user_progress.get(user_id, [])
        existing_progress = None
        
        for progress in user_progress_list:
            if progress.module_id == module_id:
                existing_progress = progress
                break
        
        if existing_progress:
            # Update existing progress
            existing_progress.status = progress_data.get("status", existing_progress.status)
            existing_progress.score = progress_data.get("score", existing_progress.score)
            existing_progress.time_spent += progress_data.get("time_spent", 0)
            existing_progress.attempts += 1
            
            if progress_data.get("status") == "completed" and not existing_progress.completion_date:
                existing_progress.completion_date = datetime.now()
            
            return existing_progress
        else:
            # Create new progress record
            new_progress = UserProgress(
                user_id=user_id,
                module_id=module_id,
                status=progress_data.get("status", "in_progress"),
                start_date=datetime.now(),
                completion_date=None,
                score=progress_data.get("score"),
                time_spent=progress_data.get("time_spent", 0),
                attempts=1
            )
            
            user_progress_list.append(new_progress)
            self.user_progress[user_id] = user_progress_list
            
            return new_progress
    
    def _check_achievements(self, user_id: str, progress: UserProgress) -> List[Dict[str, Any]]:
        """Check for new achievements"""
        achievements = []
        
        if progress.status == "completed":
            achievements.append({
                "type": "module_completed",
                "title": f"Completed {progress.module_id}",
                "description": "Great job finishing this module!",
                "points": 100
            })
        
        if progress.score and progress.score >= 90:
            achievements.append({
                "type": "high_score",
                "title": "High Achiever",
                "description": "Scored 90% or higher!",
                "points": 50
            })
        
        # Check for streaks
        streak = self._get_learning_streak(user_id)
        if streak.get("current_streak", 0) >= 7:
            achievements.append({
                "type": "streak",
                "title": "Week Warrior",
                "description": "7 days of consistent learning!",
                "points": 200
            })
        
        return achievements
    
    def _get_next_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get next module recommendations"""
        user_progress = self.user_progress.get(user_id, [])
        learning_path = self.learning_paths.get(user_id, {})
        
        completed_modules = {
            progress.module_id for progress in user_progress 
            if progress.status == "completed"
        }
        
        recommendations = []
        for module_id in learning_path.get("modules", []):
            if module_id not in completed_modules:
                module = self.learning_modules.get(module_id)
                if module and self._prerequisites_met(module, completed_modules):
                    recommendations.append({
                        "id": module.id,
                        "title": module.title,
                        "description": module.description,
                        "priority": "high" if len(recommendations) == 0 else "medium"
                    })
                    
                    if len(recommendations) >= 3:  # Limit recommendations
                        break
        
        return recommendations
    
    def _prerequisites_met(self, module: LearningModule, completed_modules: set) -> bool:
        """Check if module prerequisites are met"""
        return all(prereq in completed_modules for prereq in module.prerequisites)
    
    def _adapt_learning_path(self, user_id: str, progress: UserProgress):
        """Adapt learning path based on user performance"""
        if progress.score and progress.score < 70:
            # User struggling, might need additional practice modules
            self.logger.info(f"User {user_id} struggling with {progress.module_id}, considering path adaptation")
        elif progress.score and progress.score > 90:
            # User excelling, might skip some basic modules
            self.logger.info(f"User {user_id} excelling at {progress.module_id}, considering acceleration")
    
    def _calculate_overall_progress(self, user_id: str) -> Dict[str, Any]:
        """Calculate overall learning progress"""
        user_progress = self.user_progress.get(user_id, [])
        learning_path = self.learning_paths.get(user_id, {})
        
        total_modules = len(learning_path.get("modules", []))
        completed_modules = sum(1 for p in user_progress if p.status == "completed")
        
        if total_modules == 0:
            return {"percentage": 0, "completed": 0, "total": 0}
        
        percentage = (completed_modules / total_modules) * 100
        
        return {
            "percentage": round(percentage, 1),
            "completed": completed_modules,
            "total": total_modules,
            "current_level": self._determine_current_level(percentage)
        }
    
    def _get_learning_streak(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning streak information"""
        user_progress = self.user_progress.get(user_id, [])
        
        # Calculate streak based on completion dates
        completion_dates = [
            p.completion_date for p in user_progress 
            if p.completion_date and p.status == "completed"
        ]
        
        if not completion_dates:
            return {"current_streak": 0, "longest_streak": 0, "last_activity": None}
        
        completion_dates.sort()
        current_streak = 1
        longest_streak = 1
        
        # Simple streak calculation (consecutive days)
        for i in range(1, len(completion_dates)):
            days_diff = (completion_dates[i] - completion_dates[i-1]).days
            if days_diff <= 1:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 1
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity": completion_dates[-1] if completion_dates else None
        }
    
    def _analyze_assessment_responses(self, assessment_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze assessment responses to determine skill scores"""
        # Mock analysis - in real implementation, analyze actual responses
        return {
            "preflop_knowledge": 75.0,
            "postflop_knowledge": 60.0,
            "mathematical_skills": 80.0,
            "hand_reading": 55.0,
            "overall_score": 67.5
        }
    
    def _analyze_hand_performance(self, hand_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze hand analysis performance"""
        if not hand_results:
            return {"performance_score": 50.0}
        
        # Mock analysis
        return {
            "decision_accuracy": 70.0,
            "improvement_rate": 15.0,
            "consistency": 65.0,
            "performance_score": 68.0
        }
    
    def _combine_assessments(self, skill_scores: Dict[str, float], 
                           hand_performance: Dict[str, float]) -> Dict[str, Any]:
        """Combine different assessment results"""
        overall_score = (
            skill_scores.get("overall_score", 50) * 0.6 + 
            hand_performance.get("performance_score", 50) * 0.4
        )
        
        return {
            "overall_score": overall_score,
            "skill_breakdown": skill_scores,
            "performance_metrics": hand_performance,
            "confidence": 0.8,
            "assessment_date": datetime.now()
        }
    
    def _identify_knowledge_gaps(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify knowledge gaps from assessment"""
        gaps = []
        skill_breakdown = assessment.get("skill_breakdown", {})
        
        for skill, score in skill_breakdown.items():
            if score < 70:  # Below proficiency threshold
                gaps.append({
                    "area": skill,
                    "score": score,
                    "severity": "high" if score < 50 else "medium",
                    "recommended_modules": self._get_modules_for_skill(skill)
                })
        
        return gaps
    
    def _identify_strengths(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify user strengths from assessment"""
        strengths = []
        skill_breakdown = assessment.get("skill_breakdown", {})
        
        for skill, score in skill_breakdown.items():
            if score >= 80:  # Above proficiency threshold
                strengths.append({
                    "area": skill,
                    "score": score,
                    "level": "excellent" if score >= 90 else "good"
                })
        
        return strengths
    
    def _recommend_focus_areas(self, knowledge_gaps: List[Dict[str, Any]]) -> List[str]:
        """Recommend focus areas based on knowledge gaps"""
        focus_areas = []
        
        for gap in knowledge_gaps:
            if gap["severity"] == "high":
                focus_areas.append(gap["area"])
        
        return focus_areas[:3]  # Top 3 focus areas
    
    def _determine_next_modules(self, user_id: str, user_progress: List[UserProgress], 
                              learning_path: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine next modules for user"""
        return self._get_next_recommendations(user_id)
    
    def _suggest_practice_exercises(self, user_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest practice exercises"""
        return [
            {
                "title": "Hand Range Practice",
                "description": "Practice identifying hand ranges in different positions",
                "estimated_time": 15,
                "difficulty": "intermediate"
            },
            {
                "title": "Pot Odds Calculator",
                "description": "Practice calculating pot odds in various scenarios",
                "estimated_time": 10,
                "difficulty": "beginner"
            }
        ]
    
    def _identify_review_topics(self, user_id: str, user_progress: List[UserProgress]) -> List[str]:
        """Identify topics that need review"""
        review_topics = []
        
        for progress in user_progress:
            if progress.score and progress.score < 80:
                module = self.learning_modules.get(progress.module_id)
                if module:
                    review_topics.append(module.title)
        
        return review_topics
    
    def _create_study_schedule(self, user_id: str) -> Dict[str, Any]:
        """Create personalized study schedule"""
        return {
            "recommended_frequency": "3 times per week",
            "session_duration": "30 minutes",
            "best_times": ["evening", "weekend morning"],
            "next_session": "tomorrow"
        }
    
    def _generate_motivation_message(self, user_id: str) -> str:
        """Generate motivational message"""
        progress = self._calculate_overall_progress(user_id)
        percentage = progress.get("percentage", 0)
        
        if percentage < 25:
            return "You're just getting started! Every expert was once a beginner. Keep going!"
        elif percentage < 50:
            return "Great progress! You're building a solid foundation. Stay consistent!"
        elif percentage < 75:
            return "You're more than halfway there! Your dedication is paying off!"
        else:
            return "Amazing work! You're becoming a poker expert. Keep pushing forward!"
    
    def _determine_current_level(self, percentage: float) -> str:
        """Determine current skill level based on progress"""
        if percentage < 25:
            return "Novice"
        elif percentage < 50:
            return "Beginner"
        elif percentage < 75:
            return "Intermediate"
        else:
            return "Advanced"
    
    def _get_modules_for_skill(self, skill: str) -> List[str]:
        """Get recommended modules for specific skill"""
        skill_module_mapping = {
            "preflop_knowledge": ["starting_hands", "position_basics"],
            "postflop_knowledge": ["c_betting", "pot_odds"],
            "mathematical_skills": ["pot_odds"],
            "hand_reading": ["range_construction"]
        }
        
        return skill_module_mapping.get(skill, [])
