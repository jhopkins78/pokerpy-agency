"""
WebSocket handlers for real-time AI coach chat
Provides instant responses and typing indicators
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from src.models.coach import CoachAgent
from src.models.hand_analyzer import HandAnalyzerAgent
from src.models.base_agent import AgentMessage

class ChatHandler:
    """Handles real-time chat with AI coach"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.coach_agent = CoachAgent()
        self.hand_analyzer = HandAnalyzerAgent()
        
        # Track active sessions
        self.active_sessions = {}  # session_id -> user_data
        self.user_rooms = {}  # user_id -> room_id
        
        # Register event handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Get user info from auth or query params
                user_id = None
                if auth and 'user_id' in auth:
                    user_id = auth['user_id']
                elif request.args.get('user_id'):
                    user_id = request.args.get('user_id')
                else:
                    user_id = f"anonymous_{uuid.uuid4().hex[:8]}"
                
                session_id = request.sid
                room_id = f"user_{user_id}"
                
                # Store session info
                self.active_sessions[session_id] = {
                    'user_id': user_id,
                    'room_id': room_id,
                    'connected_at': datetime.now(),
                    'message_count': 0
                }
                
                self.user_rooms[user_id] = room_id
                
                # Join user-specific room
                join_room(room_id)
                
                # Send welcome message
                emit('connected', {
                    'status': 'connected',
                    'user_id': user_id,
                    'session_id': session_id,
                    'message': 'Connected to PokerPy AI Coach! How can I help you improve your poker game today?'
                })
                
                print(f"✅ User {user_id} connected (session: {session_id})")
                
            except Exception as e:
                print(f"❌ Connection error: {e}")
                emit('error', {'message': 'Connection failed'})
                disconnect()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            session_id = request.sid
            
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                user_id = session_data['user_id']
                
                # Clean up session data
                del self.active_sessions[session_id]
                if user_id in self.user_rooms:
                    del self.user_rooms[user_id]
                
                print(f"👋 User {user_id} disconnected (session: {session_id})")
        
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle incoming chat messages"""
            try:
                session_id = request.sid
                if session_id not in self.active_sessions:
                    emit('error', {'message': 'Session not found'})
                    return
                
                session_data = self.active_sessions[session_id]
                user_id = session_data['user_id']
                room_id = session_data['room_id']
                
                message = data.get('message', '').strip()
                if not message:
                    emit('error', {'message': 'Message cannot be empty'})
                    return
                
                # Update message count
                session_data['message_count'] += 1
                
                # Echo user message back to confirm receipt
                emit('message_received', {
                    'message': message,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id
                }, room=room_id)
                
                # Show typing indicator
                emit('coach_typing', {'typing': True}, room=room_id)
                
                # Process message with coach agent
                self.socketio.start_background_task(
                    self._process_coach_message, 
                    user_id, room_id, message, data.get('context', {})
                )
                
            except Exception as e:
                print(f"❌ Chat message error: {e}")
                emit('error', {'message': 'Failed to process message'})
        
        @self.socketio.on('analyze_hand_live')
        def handle_live_hand_analysis(data):
            """Handle live hand analysis requests"""
            try:
                session_id = request.sid
                if session_id not in self.active_sessions:
                    emit('error', {'message': 'Session not found'})
                    return
                
                session_data = self.active_sessions[session_id]
                user_id = session_data['user_id']
                room_id = session_data['room_id']
                
                hand_history = data.get('hand_history')
                if not hand_history:
                    emit('error', {'message': 'Hand history is required'})
                    return
                
                # Show analysis in progress
                emit('analysis_started', {
                    'status': 'analyzing',
                    'message': 'Analyzing your hand... This may take a moment.'
                }, room=room_id)
                
                # Process hand analysis
                self.socketio.start_background_task(
                    self._process_live_hand_analysis,
                    user_id, room_id, data
                )
                
            except Exception as e:
                print(f"❌ Live hand analysis error: {e}")
                emit('error', {'message': 'Failed to analyze hand'})
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle joining specific rooms (e.g., community discussions)"""
            try:
                room_name = data.get('room')
                if room_name:
                    join_room(room_name)
                    emit('joined_room', {'room': room_name})
                    print(f"User joined room: {room_name}")
            except Exception as e:
                print(f"❌ Join room error: {e}")
                emit('error', {'message': 'Failed to join room'})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle leaving specific rooms"""
            try:
                room_name = data.get('room')
                if room_name:
                    leave_room(room_name)
                    emit('left_room', {'room': room_name})
                    print(f"User left room: {room_name}")
            except Exception as e:
                print(f"❌ Leave room error: {e}")
                emit('error', {'message': 'Failed to leave room'})
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for connection health check"""
            emit('pong', {'timestamp': datetime.now().isoformat()})
    
    def _process_coach_message(self, user_id: str, room_id: str, message: str, context: Dict[str, Any]):
        """Process message with coach agent in background"""
        try:
            # Create message for coach agent
            agent_message = AgentMessage(
                id=f"chat_{datetime.now().timestamp()}",
                sender="websocket",
                recipient="coach",
                message_type="answer_question",
                content={
                    "question": message,
                    "user_id": user_id,
                    "context": context,
                    "is_live_chat": True
                },
                timestamp=datetime.now(),
                requires_response=True
            )
            
            # Process with coach agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(self.coach_agent.process_message(agent_message))
                
                # Stop typing indicator
                self.socketio.emit('coach_typing', {'typing': False}, room=room_id)
                
                if response and response.content:
                    # Send coach response
                    self.socketio.emit('coach_response', {
                        'message': response.content.get('response', 'I apologize, but I encountered an issue processing your question.'),
                        'suggestions': response.content.get('follow_up_suggestions', []),
                        'confidence': response.content.get('confidence', 0.8),
                        'timestamp': datetime.now().isoformat()
                    }, room=room_id)
                else:
                    self.socketio.emit('coach_response', {
                        'message': 'I apologize, but I encountered an issue processing your question. Could you please try rephrasing it?',
                        'timestamp': datetime.now().isoformat()
                    }, room=room_id)
                    
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Coach message processing error: {e}")
            self.socketio.emit('coach_typing', {'typing': False}, room=room_id)
            self.socketio.emit('error', {
                'message': 'Sorry, I encountered an error processing your message. Please try again.'
            }, room=room_id)
    
    def _process_live_hand_analysis(self, user_id: str, room_id: str, data: Dict[str, Any]):
        """Process live hand analysis in background"""
        try:
            # Create message for hand analyzer
            agent_message = AgentMessage(
                id=f"live_analysis_{datetime.now().timestamp()}",
                sender="websocket",
                recipient="hand_analyzer",
                message_type="analyze_hand",
                content={
                    "hand_history": data.get('hand_history'),
                    "player_position": data.get('player_position'),
                    "stack_size": data.get('stack_size'),
                    "analysis_depth": data.get('analysis_depth', 'basic'),
                    "is_live_analysis": True
                },
                timestamp=datetime.now(),
                requires_response=True
            )
            
            # Process with hand analyzer
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Send progress updates
                self.socketio.emit('analysis_progress', {
                    'step': 'parsing',
                    'message': 'Parsing hand history...',
                    'progress': 25
                }, room=room_id)
                
                response = loop.run_until_complete(self.hand_analyzer.process_message(agent_message))
                
                self.socketio.emit('analysis_progress', {
                    'step': 'analyzing',
                    'message': 'Analyzing decisions...',
                    'progress': 75
                }, room=room_id)
                
                if response and response.content:
                    technical_analysis = response.content
                    
                    # Get plain English explanation from coach
                    coach_message = AgentMessage(
                        id=f"live_coach_{datetime.now().timestamp()}",
                        sender="websocket",
                        recipient="coach",
                        message_type="explain_analysis",
                        content={
                            "technical_analysis": technical_analysis,
                            "user_id": user_id,
                            "skill_level": "beginner",  # Could be retrieved from user profile
                            "explanation_style": "conversational",
                            "is_live_analysis": True
                        },
                        timestamp=datetime.now(),
                        requires_response=True
                    )
                    
                    coach_response = loop.run_until_complete(self.coach_agent.process_message(coach_message))
                    
                    # Send complete analysis
                    self.socketio.emit('analysis_complete', {
                        'technical_analysis': technical_analysis,
                        'coaching_explanation': coach_response.content if coach_response else {},
                        'timestamp': datetime.now().isoformat(),
                        'analysis_id': agent_message.id
                    }, room=room_id)
                    
                else:
                    self.socketio.emit('analysis_error', {
                        'message': 'Failed to analyze hand. Please check your hand history format.'
                    }, room=room_id)
                    
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Live hand analysis error: {e}")
            self.socketio.emit('analysis_error', {
                'message': 'An error occurred during hand analysis. Please try again.'
            }, room=room_id)
    
    def broadcast_to_user(self, user_id: str, event: str, data: Dict[str, Any]):
        """Broadcast message to specific user"""
        if user_id in self.user_rooms:
            room_id = self.user_rooms[user_id]
            self.socketio.emit(event, data, room=room_id)
    
    def broadcast_to_all(self, event: str, data: Dict[str, Any]):
        """Broadcast message to all connected users"""
        self.socketio.emit(event, data, broadcast=True)
    
    def get_active_users(self) -> int:
        """Get count of active users"""
        return len(self.active_sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self.active_sessions.get(session_id)

class CommunityHandler:
    """Handles real-time community features"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.register_handlers()
    
    def register_handlers(self):
        """Register community WebSocket handlers"""
        
        @self.socketio.on('join_community')
        def handle_join_community(data):
            """Join community room for live updates"""
            try:
                join_room('community')
                emit('joined_community', {
                    'status': 'joined',
                    'message': 'You are now receiving live community updates!'
                })
            except Exception as e:
                print(f"❌ Join community error: {e}")
                emit('error', {'message': 'Failed to join community'})
        
        @self.socketio.on('leave_community')
        def handle_leave_community():
            """Leave community room"""
            try:
                leave_room('community')
                emit('left_community', {'status': 'left'})
            except Exception as e:
                print(f"❌ Leave community error: {e}")
    
    def notify_new_post(self, post_data: Dict[str, Any]):
        """Notify community of new post"""
        self.socketio.emit('new_post', {
            'post': post_data,
            'timestamp': datetime.now().isoformat()
        }, room='community')
    
    def notify_new_comment(self, comment_data: Dict[str, Any]):
        """Notify community of new comment"""
        self.socketio.emit('new_comment', {
            'comment': comment_data,
            'timestamp': datetime.now().isoformat()
        }, room='community')

class ProgressHandler:
    """Handles real-time learning progress updates"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.register_handlers()
    
    def register_handlers(self):
        """Register progress WebSocket handlers"""
        
        @self.socketio.on('subscribe_progress')
        def handle_subscribe_progress(data):
            """Subscribe to progress updates"""
            try:
                user_id = data.get('user_id')
                if user_id:
                    join_room(f'progress_{user_id}')
                    emit('subscribed_progress', {
                        'status': 'subscribed',
                        'user_id': user_id
                    })
            except Exception as e:
                print(f"❌ Subscribe progress error: {e}")
                emit('error', {'message': 'Failed to subscribe to progress updates'})
    
    def notify_progress_update(self, user_id: str, progress_data: Dict[str, Any]):
        """Notify user of progress update"""
        self.socketio.emit('progress_update', {
            'progress': progress_data,
            'timestamp': datetime.now().isoformat()
        }, room=f'progress_{user_id}')
    
    def notify_achievement(self, user_id: str, achievement_data: Dict[str, Any]):
        """Notify user of new achievement"""
        self.socketio.emit('achievement_unlocked', {
            'achievement': achievement_data,
            'timestamp': datetime.now().isoformat()
        }, room=f'progress_{user_id}')

def create_websocket_handlers(socketio: SocketIO) -> Dict[str, Any]:
    """Create and return all WebSocket handlers"""
    chat_handler = ChatHandler(socketio)
    community_handler = CommunityHandler(socketio)
    progress_handler = ProgressHandler(socketio)
    
    return {
        'chat': chat_handler,
        'community': community_handler,
        'progress': progress_handler
    }
