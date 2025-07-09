"""
Community Agent for PokerPy
Manages community features, user interactions, and social elements
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .base_agent import BaseAgent, AgentMessage, AgentCapability

class PostType(Enum):
    HAND_SHARE = "hand_share"
    SUCCESS_STORY = "success_story"
    QUESTION = "question"
    TIP = "tip"
    DISCUSSION = "discussion"

class ModerationStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"

@dataclass
class CommunityPost:
    """Represents a community post"""
    id: str
    user_id: str
    username: str
    post_type: PostType
    title: str
    content: str
    hand_data: Optional[Dict[str, Any]]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    likes: int
    comments: int
    moderation_status: ModerationStatus
    is_anonymous: bool

@dataclass
class Comment:
    """Represents a comment on a post"""
    id: str
    post_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    likes: int
    is_anonymous: bool

@dataclass
class UserReputation:
    """Tracks user reputation in the community"""
    user_id: str
    reputation_score: int
    helpful_answers: int
    posts_created: int
    comments_made: int
    likes_received: int
    badges: List[str]
    level: str

class CommunityAgent(BaseAgent):
    """
    Manages community features including posts, comments, moderation, and user reputation
    Provides social learning and peer support functionality
    """
    
    def __init__(self):
        super().__init__(
            agent_id="community",
            name="Community Manager",
            description="Manages community features and user interactions"
        )
        
        # Community data storage
        self.posts = {}  # post_id -> CommunityPost
        self.comments = {}  # comment_id -> Comment
        self.user_reputations = {}  # user_id -> UserReputation
        self.user_interactions = {}  # user_id -> interaction history
        
        # Moderation settings
        self.auto_moderation_enabled = True
        self.flagged_keywords = ["spam", "inappropriate", "offensive"]
        self.reputation_thresholds = {
            "newbie": 0,
            "contributor": 100,
            "expert": 500,
            "mentor": 1000,
            "legend": 2000
        }
        
        # Community guidelines
        self.community_guidelines = {
            "be_respectful": "Treat all community members with respect",
            "stay_on_topic": "Keep discussions poker-related",
            "no_spam": "Don't post repetitive or promotional content",
            "help_others": "Share knowledge and help fellow players improve",
            "constructive_feedback": "Provide constructive criticism and feedback"
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="create_post",
                description="Create a new community post",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "username": {"type": "string"},
                        "post_type": {"type": "string", "enum": ["hand_share", "success_story", "question", "tip", "discussion"]},
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "hand_data": {"type": "object"},
                        "tags": {"type": "array"},
                        "is_anonymous": {"type": "boolean"}
                    },
                    "required": ["user_id", "username", "post_type", "title", "content"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string"},
                        "moderation_status": {"type": "string"},
                        "estimated_reach": {"type": "number"}
                    }
                }
            ),
            AgentCapability(
                name="get_community_feed",
                description="Get personalized community feed for user",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "feed_type": {"type": "string", "enum": ["trending", "recent", "following", "recommended"]},
                        "filters": {"type": "object"},
                        "limit": {"type": "number"},
                        "offset": {"type": "number"}
                    },
                    "required": ["user_id"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "posts": {"type": "array"},
                        "total_count": {"type": "number"},
                        "has_more": {"type": "boolean"}
                    }
                }
            ),
            AgentCapability(
                name="moderate_content",
                description="Moderate community content for appropriateness",
                input_schema={
                    "type": "object",
                    "properties": {
                        "content_id": {"type": "string"},
                        "content_type": {"type": "string", "enum": ["post", "comment"]},
                        "moderation_action": {"type": "string", "enum": ["approve", "reject", "flag", "auto_moderate"]}
                    },
                    "required": ["content_id", "content_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "moderation_result": {"type": "string"},
                        "confidence_score": {"type": "number"},
                        "reasons": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="manage_user_reputation",
                description="Update and manage user reputation scores",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "action": {"type": "string"},
                        "points": {"type": "number"},
                        "reason": {"type": "string"}
                    },
                    "required": ["user_id", "action"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "new_reputation": {"type": "object"},
                        "badges_earned": {"type": "array"},
                        "level_change": {"type": "boolean"}
                    }
                }
            ),
            AgentCapability(
                name="generate_insights",
                description="Generate community insights and analytics",
                input_schema={
                    "type": "object",
                    "properties": {
                        "insight_type": {"type": "string", "enum": ["engagement", "trending_topics", "user_activity", "content_quality"]},
                        "time_period": {"type": "string"},
                        "filters": {"type": "object"}
                    },
                    "required": ["insight_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "insights": {"type": "object"},
                        "metrics": {"type": "object"},
                        "recommendations": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process community management requests"""
        try:
            message_type = message.message_type
            content = message.content
            
            if message_type == "create_post":
                result = await self._create_post(content)
            elif message_type == "get_community_feed":
                result = await self._get_community_feed(content)
            elif message_type == "moderate_content":
                result = await self._moderate_content(content)
            elif message_type == "manage_user_reputation":
                result = await self._manage_user_reputation(content)
            elif message_type == "generate_insights":
                result = await self._generate_insights(content)
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
            self.logger.error(f"Error processing community message: {e}")
            return AgentMessage(
                id=f"error_{message.id}",
                sender=self.agent_id,
                recipient=message.sender,
                message_type="error",
                content={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _create_post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new community post"""
        user_id = data.get("user_id")
        username = data.get("username")
        post_type = PostType(data.get("post_type"))
        title = data.get("title")
        content = data.get("content")
        hand_data = data.get("hand_data")
        tags = data.get("tags", [])
        is_anonymous = data.get("is_anonymous", False)
        
        # Generate post ID
        post_id = f"post_{datetime.now().timestamp()}_{user_id}"
        
        # Create post object
        post = CommunityPost(
            id=post_id,
            user_id=user_id,
            username=username if not is_anonymous else "Anonymous",
            post_type=post_type,
            title=title,
            content=content,
            hand_data=hand_data,
            tags=tags,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            likes=0,
            comments=0,
            moderation_status=ModerationStatus.PENDING,
            is_anonymous=is_anonymous
        )
        
        # Auto-moderate content
        moderation_result = await self._auto_moderate_post(post)
        post.moderation_status = ModerationStatus(moderation_result["status"])
        
        # Store post
        self.posts[post_id] = post
        
        # Update user reputation
        await self._update_reputation(user_id, "post_created", 10, "Created a community post")
        
        # Estimate reach
        estimated_reach = self._estimate_post_reach(post)
        
        return {
            "post_id": post_id,
            "moderation_status": post.moderation_status.value,
            "estimated_reach": estimated_reach,
            "created_at": post.created_at.isoformat(),
            "auto_moderation_score": moderation_result.get("confidence", 0.8)
        }
    
    async def _get_community_feed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized community feed"""
        user_id = data.get("user_id")
        feed_type = data.get("feed_type", "recommended")
        filters = data.get("filters", {})
        limit = data.get("limit", 20)
        offset = data.get("offset", 0)
        
        # Get user preferences and history
        user_reputation = self.user_reputations.get(user_id)
        user_interactions = self.user_interactions.get(user_id, {})
        
        # Filter and sort posts based on feed type
        filtered_posts = self._filter_posts(feed_type, filters, user_id, user_reputation)
        sorted_posts = self._sort_posts(filtered_posts, feed_type, user_interactions)
        
        # Paginate results
        paginated_posts = sorted_posts[offset:offset + limit]
        
        # Convert to serializable format
        post_data = []
        for post in paginated_posts:
            post_dict = asdict(post)
            post_dict["created_at"] = post.created_at.isoformat()
            post_dict["updated_at"] = post.updated_at.isoformat()
            post_dict["post_type"] = post.post_type.value
            post_dict["moderation_status"] = post.moderation_status.value
            
            # Add engagement metrics
            post_dict["engagement_score"] = self._calculate_engagement_score(post)
            post_dict["is_trending"] = self._is_trending(post)
            
            post_data.append(post_dict)
        
        return {
            "posts": post_data,
            "total_count": len(filtered_posts),
            "has_more": offset + limit < len(filtered_posts),
            "feed_metadata": {
                "feed_type": feed_type,
                "personalization_score": self._calculate_personalization_score(user_id, paginated_posts)
            }
        }
    
    async def _moderate_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Moderate community content"""
        content_id = data.get("content_id")
        content_type = data.get("content_type")
        moderation_action = data.get("moderation_action", "auto_moderate")
        
        if content_type == "post":
            content_obj = self.posts.get(content_id)
        elif content_type == "comment":
            content_obj = self.comments.get(content_id)
        else:
            return {"error": "Invalid content type"}
        
        if not content_obj:
            return {"error": "Content not found"}
        
        # Perform moderation
        if moderation_action == "auto_moderate":
            if content_type == "post":
                result = await self._auto_moderate_post(content_obj)
            else:
                result = await self._auto_moderate_comment(content_obj)
        else:
            result = await self._manual_moderate(content_obj, moderation_action)
        
        # Update content status
        if hasattr(content_obj, 'moderation_status'):
            content_obj.moderation_status = ModerationStatus(result["status"])
        
        return {
            "moderation_result": result["status"],
            "confidence_score": result.get("confidence", 0.8),
            "reasons": result.get("reasons", []),
            "action_taken": result.get("action_taken", "none")
        }
    
    async def _manage_user_reputation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user reputation"""
        user_id = data.get("user_id")
        action = data.get("action")
        points = data.get("points", 0)
        reason = data.get("reason", "")
        
        # Get or create user reputation
        if user_id not in self.user_reputations:
            self.user_reputations[user_id] = UserReputation(
                user_id=user_id,
                reputation_score=0,
                helpful_answers=0,
                posts_created=0,
                comments_made=0,
                likes_received=0,
                badges=[],
                level="newbie"
            )
        
        reputation = self.user_reputations[user_id]
        old_level = reputation.level
        
        # Update reputation based on action
        if action == "post_created":
            reputation.posts_created += 1
            reputation.reputation_score += points
        elif action == "comment_made":
            reputation.comments_made += 1
            reputation.reputation_score += points
        elif action == "received_like":
            reputation.likes_received += 1
            reputation.reputation_score += points
        elif action == "helpful_answer":
            reputation.helpful_answers += 1
            reputation.reputation_score += points
        elif action == "penalty":
            reputation.reputation_score = max(0, reputation.reputation_score - abs(points))
        
        # Update level based on reputation score
        new_level = self._calculate_user_level(reputation.reputation_score)
        level_changed = new_level != old_level
        reputation.level = new_level
        
        # Check for new badges
        new_badges = self._check_for_badges(reputation)
        
        return {
            "new_reputation": asdict(reputation),
            "badges_earned": new_badges,
            "level_change": level_changed,
            "points_change": points,
            "reason": reason
        }
    
    async def _generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate community insights"""
        insight_type = data.get("insight_type")
        time_period = data.get("time_period", "week")
        filters = data.get("filters", {})
        
        if insight_type == "engagement":
            return await self._generate_engagement_insights(time_period, filters)
        elif insight_type == "trending_topics":
            return await self._generate_trending_insights(time_period, filters)
        elif insight_type == "user_activity":
            return await self._generate_user_activity_insights(time_period, filters)
        elif insight_type == "content_quality":
            return await self._generate_content_quality_insights(time_period, filters)
        else:
            return {"error": "Unknown insight type"}
    
    async def _auto_moderate_post(self, post: CommunityPost) -> Dict[str, Any]:
        """Auto-moderate a post"""
        confidence = 0.8
        reasons = []
        status = "approved"
        
        # Check for flagged keywords
        content_lower = (post.title + " " + post.content).lower()
        for keyword in self.flagged_keywords:
            if keyword in content_lower:
                status = "flagged"
                reasons.append(f"Contains flagged keyword: {keyword}")
                confidence = 0.9
        
        # Check content length
        if len(post.content) < 10:
            status = "flagged"
            reasons.append("Content too short")
            confidence = 0.7
        
        # Check for spam patterns
        if self._detect_spam_patterns(post):
            status = "flagged"
            reasons.append("Potential spam detected")
            confidence = 0.85
        
        return {
            "status": status,
            "confidence": confidence,
            "reasons": reasons,
            "action_taken": "auto_moderated"
        }
    
    async def _auto_moderate_comment(self, comment: Comment) -> Dict[str, Any]:
        """Auto-moderate a comment"""
        confidence = 0.8
        reasons = []
        status = "approved"
        
        # Similar logic to post moderation but for comments
        content_lower = comment.content.lower()
        for keyword in self.flagged_keywords:
            if keyword in content_lower:
                status = "flagged"
                reasons.append(f"Contains flagged keyword: {keyword}")
                confidence = 0.9
        
        return {
            "status": status,
            "confidence": confidence,
            "reasons": reasons,
            "action_taken": "auto_moderated"
        }
    
    async def _manual_moderate(self, content_obj: Any, action: str) -> Dict[str, Any]:
        """Perform manual moderation"""
        return {
            "status": action,
            "confidence": 1.0,
            "reasons": [f"Manual moderation: {action}"],
            "action_taken": "manual_moderation"
        }
    
    def _filter_posts(self, feed_type: str, filters: Dict[str, Any], 
                     user_id: str, user_reputation: Optional[UserReputation]) -> List[CommunityPost]:
        """Filter posts based on feed type and filters"""
        all_posts = list(self.posts.values())
        
        # Filter by moderation status
        filtered_posts = [p for p in all_posts if p.moderation_status == ModerationStatus.APPROVED]
        
        # Apply additional filters based on feed type
        if feed_type == "trending":
            # Filter for trending posts (high engagement in last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            filtered_posts = [p for p in filtered_posts if p.created_at >= cutoff_time]
        elif feed_type == "recent":
            # Sort by creation time (handled in sorting)
            pass
        elif feed_type == "recommended":
            # Personalized recommendations based on user interests
            if user_reputation:
                # Filter based on user's interaction history and preferences
                pass
        
        # Apply custom filters
        if "post_type" in filters:
            post_types = filters["post_type"]
            if not isinstance(post_types, list):
                post_types = [post_types]
            filtered_posts = [p for p in filtered_posts if p.post_type.value in post_types]
        
        if "tags" in filters:
            required_tags = filters["tags"]
            if not isinstance(required_tags, list):
                required_tags = [required_tags]
            filtered_posts = [p for p in filtered_posts if any(tag in p.tags for tag in required_tags)]
        
        return filtered_posts
    
    def _sort_posts(self, posts: List[CommunityPost], feed_type: str, 
                   user_interactions: Dict[str, Any]) -> List[CommunityPost]:
        """Sort posts based on feed type"""
        if feed_type == "trending":
            # Sort by engagement score
            return sorted(posts, key=lambda p: self._calculate_engagement_score(p), reverse=True)
        elif feed_type == "recent":
            # Sort by creation time
            return sorted(posts, key=lambda p: p.created_at, reverse=True)
        elif feed_type == "recommended":
            # Sort by personalization score
            return sorted(posts, key=lambda p: self._calculate_personalization_score_for_post(p, user_interactions), reverse=True)
        else:
            # Default to recent
            return sorted(posts, key=lambda p: p.created_at, reverse=True)
    
    def _calculate_engagement_score(self, post: CommunityPost) -> float:
        """Calculate engagement score for a post"""
        # Simple engagement calculation
        age_hours = (datetime.now() - post.created_at).total_seconds() / 3600
        age_factor = max(0.1, 1 / (1 + age_hours / 24))  # Decay over time
        
        engagement = (post.likes * 2 + post.comments * 3) * age_factor
        return engagement
    
    def _is_trending(self, post: CommunityPost) -> bool:
        """Check if a post is trending"""
        engagement_score = self._calculate_engagement_score(post)
        age_hours = (datetime.now() - post.created_at).total_seconds() / 3600
        
        # Trending if high engagement and recent
        return engagement_score > 10 and age_hours < 48
    
    def _calculate_personalization_score(self, user_id: str, posts: List[CommunityPost]) -> float:
        """Calculate personalization score for feed"""
        if not posts:
            return 0.0
        
        # Mock personalization score
        return 0.75
    
    def _calculate_personalization_score_for_post(self, post: CommunityPost, 
                                                user_interactions: Dict[str, Any]) -> float:
        """Calculate personalization score for a specific post"""
        score = 0.5  # Base score
        
        # Boost score based on user's interaction history
        liked_tags = user_interactions.get("liked_tags", [])
        for tag in post.tags:
            if tag in liked_tags:
                score += 0.1
        
        # Boost score for post types user engages with
        preferred_types = user_interactions.get("preferred_post_types", [])
        if post.post_type.value in preferred_types:
            score += 0.2
        
        return min(1.0, score)
    
    def _estimate_post_reach(self, post: CommunityPost) -> int:
        """Estimate potential reach of a post"""
        base_reach = 50  # Base reach for all posts
        
        # Adjust based on post type
        type_multipliers = {
            PostType.HAND_SHARE: 1.2,
            PostType.SUCCESS_STORY: 1.5,
            PostType.QUESTION: 1.0,
            PostType.TIP: 1.3,
            PostType.DISCUSSION: 1.1
        }
        
        multiplier = type_multipliers.get(post.post_type, 1.0)
        estimated_reach = int(base_reach * multiplier)
        
        return estimated_reach
    
    def _detect_spam_patterns(self, post: CommunityPost) -> bool:
        """Detect spam patterns in post"""
        # Simple spam detection
        content = post.title + " " + post.content
        
        # Check for excessive capitalization
        if sum(1 for c in content if c.isupper()) / len(content) > 0.5:
            return True
        
        # Check for excessive repetition
        words = content.lower().split()
        if len(set(words)) / len(words) < 0.5:  # Less than 50% unique words
            return True
        
        return False
    
    async def _update_reputation(self, user_id: str, action: str, points: int, reason: str):
        """Update user reputation"""
        await self._manage_user_reputation({
            "user_id": user_id,
            "action": action,
            "points": points,
            "reason": reason
        })
    
    def _calculate_user_level(self, reputation_score: int) -> str:
        """Calculate user level based on reputation score"""
        for level, threshold in reversed(list(self.reputation_thresholds.items())):
            if reputation_score >= threshold:
                return level
        return "newbie"
    
    def _check_for_badges(self, reputation: UserReputation) -> List[str]:
        """Check for new badges earned"""
        new_badges = []
        
        # First post badge
        if reputation.posts_created >= 1 and "first_post" not in reputation.badges:
            new_badges.append("first_post")
            reputation.badges.append("first_post")
        
        # Helpful member badge
        if reputation.helpful_answers >= 10 and "helpful_member" not in reputation.badges:
            new_badges.append("helpful_member")
            reputation.badges.append("helpful_member")
        
        # Popular contributor badge
        if reputation.likes_received >= 50 and "popular_contributor" not in reputation.badges:
            new_badges.append("popular_contributor")
            reputation.badges.append("popular_contributor")
        
        # Active participant badge
        if reputation.comments_made >= 25 and "active_participant" not in reputation.badges:
            new_badges.append("active_participant")
            reputation.badges.append("active_participant")
        
        return new_badges
    
    async def _generate_engagement_insights(self, time_period: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate engagement insights"""
        # Mock engagement insights
        return {
            "insights": {
                "total_posts": 150,
                "total_comments": 450,
                "total_likes": 1200,
                "average_engagement_rate": 0.15,
                "top_engaging_post_types": ["success_story", "hand_share", "tip"]
            },
            "metrics": {
                "posts_per_day": 21.4,
                "comments_per_post": 3.0,
                "likes_per_post": 8.0,
                "active_users": 75
            },
            "recommendations": [
                "Encourage more success story posts",
                "Create weekly discussion threads",
                "Implement gamification for engagement"
            ]
        }
    
    async def _generate_trending_insights(self, time_period: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trending topics insights"""
        return {
            "insights": {
                "trending_tags": ["position-play", "bluffing", "bankroll-management"],
                "trending_post_types": ["question", "tip"],
                "viral_posts": ["post_123", "post_456"],
                "emerging_topics": ["GTO strategy", "live poker"]
            },
            "metrics": {
                "tag_growth_rates": {"position-play": 0.25, "bluffing": 0.18},
                "topic_engagement_scores": {"position-play": 8.5, "bluffing": 7.2}
            },
            "recommendations": [
                "Create content around trending topics",
                "Feature trending posts in newsletter",
                "Organize discussions on emerging topics"
            ]
        }
    
    async def _generate_user_activity_insights(self, time_period: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate user activity insights"""
        return {
            "insights": {
                "most_active_users": ["user_123", "user_456", "user_789"],
                "user_retention_rate": 0.68,
                "new_user_engagement": 0.45,
                "peak_activity_hours": ["19:00", "20:00", "21:00"]
            },
            "metrics": {
                "daily_active_users": 45,
                "weekly_active_users": 120,
                "monthly_active_users": 280,
                "average_session_duration": "12 minutes"
            },
            "recommendations": [
                "Send notifications during peak hours",
                "Create onboarding program for new users",
                "Recognize most active contributors"
            ]
        }
    
    async def _generate_content_quality_insights(self, time_period: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content quality insights"""
        return {
            "insights": {
                "average_content_score": 7.2,
                "high_quality_posts_percentage": 0.65,
                "moderation_approval_rate": 0.92,
                "user_satisfaction_score": 8.1
            },
            "metrics": {
                "posts_flagged": 12,
                "posts_approved": 138,
                "average_post_length": 245,
                "helpful_answers_ratio": 0.78
            },
            "recommendations": [
                "Provide content creation guidelines",
                "Implement peer review system",
                "Reward high-quality contributions"
            ]
        }

