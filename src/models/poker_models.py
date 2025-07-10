"""
Database models for PokerPy
Defines data structures for users, hands, learning progress, and community features
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import json

db = SQLAlchemy()

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

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

class User(db.Model):
    """User model for authentication and profile data"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    skill_level = db.Column(db.Enum(SkillLevel), default=SkillLevel.BEGINNER)
    preferred_game = db.Column(db.String(50), default="No Limit Hold'em")
    timezone = db.Column(db.String(50), default="UTC")
    
    # Preferences
    coaching_style = db.Column(db.String(20), default="encouraging")  # encouraging, direct, analytical
    explanation_style = db.Column(db.String(20), default="simple")  # simple, detailed, conversational
    learning_pace = db.Column(db.String(20), default="moderate")  # light, moderate, intensive
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    hand_analyses = db.relationship('HandAnalysis', backref='user', lazy=True, cascade='all, delete-orphan')
    learning_progress = db.relationship('LearningProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    community_posts = db.relationship('CommunityPost', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'skill_level': self.skill_level.value if self.skill_level else None,
            'preferred_game': self.preferred_game,
            'coaching_style': self.coaching_style,
            'explanation_style': self.explanation_style,
            'learning_pace': self.learning_pace,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class HandAnalysis(db.Model):
    """Stores hand analysis results and coaching feedback"""
    __tablename__ = 'hand_analyses'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Hand data
    hand_history = db.Column(db.Text, nullable=False)
    player_position = db.Column(db.String(10))
    stack_size = db.Column(db.Float)
    game_type = db.Column(db.String(50), default="No Limit Hold'em")
    
    # Analysis results
    technical_analysis = db.Column(db.JSON)  # Raw technical analysis from HandAnalyzerAgent
    coaching_explanation = db.Column(db.JSON)  # Plain English explanation from CoachAgent
    key_decisions = db.Column(db.JSON)  # List of key decision points
    identified_mistakes = db.Column(db.JSON)  # List of mistakes found
    recommendations = db.Column(db.JSON)  # List of recommendations
    
    # Metadata
    analysis_depth = db.Column(db.String(20), default="basic")  # basic, intermediate, advanced
    confidence_score = db.Column(db.Float)  # AI confidence in analysis
    processing_time = db.Column(db.Float)  # Time taken to analyze
    
    # User feedback
    user_rating = db.Column(db.Integer)  # 1-5 rating of analysis quality
    user_feedback = db.Column(db.Text)  # User comments on analysis
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hand_history': self.hand_history,
            'player_position': self.player_position,
            'stack_size': self.stack_size,
            'game_type': self.game_type,
            'technical_analysis': self.technical_analysis,
            'coaching_explanation': self.coaching_explanation,
            'key_decisions': self.key_decisions,
            'identified_mistakes': self.identified_mistakes,
            'recommendations': self.recommendations,
            'analysis_depth': self.analysis_depth,
            'confidence_score': self.confidence_score,
            'user_rating': self.user_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LearningModule(db.Model):
    """Learning curriculum modules"""
    __tablename__ = 'learning_modules'
    
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.Enum(SkillLevel), nullable=False)
    estimated_time = db.Column(db.Integer)  # minutes
    content_type = db.Column(db.String(20))  # video, article, exercise, quiz
    content_url = db.Column(db.String(500))
    tags = db.Column(db.JSON)  # List of tags
    prerequisites = db.Column(db.JSON)  # List of prerequisite module IDs
    
    # Content metadata
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty.value if self.difficulty else None,
            'estimated_time': self.estimated_time,
            'content_type': self.content_type,
            'content_url': self.content_url,
            'tags': self.tags,
            'prerequisites': self.prerequisites,
            'is_active': self.is_active,
            'order_index': self.order_index
        }

class LearningProgress(db.Model):
    """Tracks user progress through learning modules"""
    __tablename__ = 'learning_progress'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.String(50), db.ForeignKey('learning_modules.id'), nullable=False)
    
    # Progress tracking
    status = db.Column(db.String(20), default="not_started")  # not_started, in_progress, completed, mastered
    progress_percentage = db.Column(db.Float, default=0.0)
    time_spent = db.Column(db.Integer, default=0)  # minutes
    attempts = db.Column(db.Integer, default=0)
    
    # Performance metrics
    score = db.Column(db.Float)  # Quiz/exercise score
    completion_time = db.Column(db.Integer)  # Time to complete in minutes
    
    # Timestamps
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    module = db.relationship('LearningModule', backref='user_progress')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'module_id': self.module_id,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'time_spent': self.time_spent,
            'attempts': self.attempts,
            'score': self.score,
            'completion_time': self.completion_time,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

class UserReputation(db.Model):
    """Tracks user reputation in the community"""
    __tablename__ = 'user_reputations'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Reputation metrics
    reputation_score = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20), default="newbie")  # newbie, contributor, expert, mentor, legend
    
    # Activity counters
    posts_created = db.Column(db.Integer, default=0)
    comments_made = db.Column(db.Integer, default=0)
    likes_received = db.Column(db.Integer, default=0)
    helpful_answers = db.Column(db.Integer, default=0)
    
    # Badges and achievements
    badges = db.Column(db.JSON, default=list)  # List of earned badges
    achievements = db.Column(db.JSON, default=list)  # List of achievements
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reputation', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reputation_score': self.reputation_score,
            'level': self.level,
            'posts_created': self.posts_created,
            'comments_made': self.comments_made,
            'likes_received': self.likes_received,
            'helpful_answers': self.helpful_answers,
            'badges': self.badges,
            'achievements': self.achievements,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CommunityPost(db.Model):
    """Community posts for sharing hands, tips, and discussions"""
    __tablename__ = 'community_posts'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Post content
    post_type = db.Column(db.Enum(PostType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    hand_data = db.Column(db.JSON)  # For hand_share posts
    tags = db.Column(db.JSON, default=list)
    
    # Moderation
    moderation_status = db.Column(db.Enum(ModerationStatus), default=ModerationStatus.PENDING)
    moderation_notes = db.Column(db.Text)
    
    # Engagement metrics
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    
    # Settings
    is_anonymous = db.Column(db.Boolean, default=False)
    allow_comments = db.Column(db.Boolean, default=True)
    is_pinned = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user and not self.is_anonymous else "Anonymous",
            'post_type': self.post_type.value if self.post_type else None,
            'title': self.title,
            'content': self.content,
            'hand_data': self.hand_data,
            'tags': self.tags,
            'moderation_status': self.moderation_status.value if self.moderation_status else None,
            'likes': self.likes,
            'views': self.views,
            'shares': self.shares,
            'comment_count': len(self.comments) if self.comments else 0,
            'is_anonymous': self.is_anonymous,
            'allow_comments': self.allow_comments,
            'is_pinned': self.is_pinned,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Comment(db.Model):
    """Comments on community posts"""
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True)
    post_id = db.Column(db.String(36), db.ForeignKey('community_posts.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    parent_comment_id = db.Column(db.String(36), db.ForeignKey('comments.id'))  # For nested comments
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    
    # Moderation
    moderation_status = db.Column(db.Enum(ModerationStatus), default=ModerationStatus.APPROVED)
    
    # Engagement
    likes = db.Column(db.Integer, default=0)
    
    # Settings
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    replies = db.relationship('Comment', backref=db.backref('parent_comment', remote_side=[id]), lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user and not self.is_anonymous else "Anonymous",
            'parent_comment_id': self.parent_comment_id,
            'content': self.content,
            'moderation_status': self.moderation_status.value if self.moderation_status else None,
            'likes': self.likes,
            'is_anonymous': self.is_anonymous,
            'reply_count': len(self.replies) if self.replies else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserSession(db.Model):
    """Tracks user sessions for analytics"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Session data
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Activity tracking
    pages_visited = db.Column(db.JSON, default=list)
    actions_performed = db.Column(db.JSON, default=list)
    hands_analyzed = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)  # seconds
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'hands_analyzed': self.hands_analyzed,
            'time_spent': self.time_spent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }

class SystemMetrics(db.Model):
    """System performance and usage metrics"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.String(36), primary_key=True)
    
    # Metrics data
    metric_type = db.Column(db.String(50), nullable=False)  # daily_users, hand_analyses, etc.
    metric_value = db.Column(db.Float, nullable=False)
    metric_data = db.Column(db.JSON)  # Additional metric details
    
    # Time period
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer)  # For hourly metrics
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'metric_data': self.metric_data,
            'date': self.date.isoformat() if self.date else None,
            'hour': self.hour,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

