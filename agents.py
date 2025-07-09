"""
Flask routes for PokerPy Agentic System API
Exposes agent functionality through REST endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import json
from typing import Dict, Any

from src.agents import (
    AgentOrchestrator, 
    HandAnalyzerAgent, 
    CoachAgent, 
    LearningPathAgent, 
    CommunityAgent,
    AgentMessage
)

# Create blueprint
agents_bp = Blueprint('agents', __name__)

# Initialize orchestrator and agents
orchestrator = AgentOrchestrator()
hand_analyzer = HandAnalyzerAgent()
coach = CoachAgent()
learning_path = LearningPathAgent()
community = CommunityAgent()

# Register agents with orchestrator
orchestrator.register_agent(hand_analyzer)
orchestrator.register_agent(coach)
orchestrator.register_agent(learning_path)
orchestrator.register_agent(community)

# Define workflows
orchestrator.define_workflow("analyze_and_coach", [
    "hand_analyzer", "coach"
])
orchestrator.define_workflow("full_analysis", [
    "hand_analyzer", "coach", "learning_path"
])

@agents_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": orchestrator.get_agent_status()
    })

@agents_bp.route('/analyze-hand', methods=['POST'])
def analyze_hand():
    """Analyze a poker hand and provide coaching"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'hand_history' not in data:
            return jsonify({"error": "hand_history is required"}), 400
        
        user_id = data.get('user_id', 'anonymous')
        skill_level = data.get('skill_level', 'beginner')
        
        # Create analysis request
        analysis_data = {
            "hand_history": data['hand_history'],
            "player_position": data.get('player_position'),
            "stack_size": data.get('stack_size'),
            "analysis_depth": data.get('analysis_depth', 'basic')
        }
        
        # Send to hand analyzer
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Create message for hand analyzer
            message = AgentMessage(
                id=f"analyze_{datetime.now().timestamp()}",
                sender="api",
                recipient="hand_analyzer",
                message_type="analyze_hand",
                content=analysis_data,
                timestamp=datetime.now(),
                requires_response=True
            )
            
            # Process message
            response = loop.run_until_complete(hand_analyzer.process_message(message))
            
            if response and response.content:
                technical_analysis = response.content
                
                # Send to coach for plain English explanation
                coach_message = AgentMessage(
                    id=f"coach_{datetime.now().timestamp()}",
                    sender="api",
                    recipient="coach",
                    message_type="explain_analysis",
                    content={
                        "technical_analysis": technical_analysis,
                        "user_id": user_id,
                        "skill_level": skill_level,
                        "explanation_style": "conversational"
                    },
                    timestamp=datetime.now(),
                    requires_response=True
                )
                
                coach_response = loop.run_until_complete(coach.process_message(coach_message))
                
                return jsonify({
                    "success": True,
                    "technical_analysis": technical_analysis,
                    "coaching_explanation": coach_response.content if coach_response else {},
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to analyze hand"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/ask-coach', methods=['POST'])
def ask_coach():
    """Ask the AI coach a question"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({"error": "question is required"}), 400
        
        user_id = data.get('user_id', 'anonymous')
        question = data['question']
        context = data.get('context', {})
        
        # Create message for coach
        message = AgentMessage(
            id=f"question_{datetime.now().timestamp()}",
            sender="api",
            recipient="coach",
            message_type="answer_question",
            content={
                "question": question,
                "user_id": user_id,
                "context": context
            },
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(coach.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "answer": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to get answer from coach"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/learning-path', methods=['POST'])
def create_learning_path():
    """Create personalized learning path"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({"error": "user_id is required"}), 400
        
        # Create message for learning path agent
        message = AgentMessage(
            id=f"learning_path_{datetime.now().timestamp()}",
            sender="api",
            recipient="learning_path",
            message_type="create_learning_path",
            content=data,
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(learning_path.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "learning_path": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to create learning path"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/learning-progress', methods=['POST'])
def track_learning_progress():
    """Track user progress through learning modules"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'module_id', 'progress_data']
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Required fields: {required_fields}"}), 400
        
        # Create message for learning path agent
        message = AgentMessage(
            id=f"progress_{datetime.now().timestamp()}",
            sender="api",
            recipient="learning_path",
            message_type="track_progress",
            content=data,
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(learning_path.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "progress_update": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to track progress"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/community/posts', methods=['POST'])
def create_community_post():
    """Create a new community post"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'username', 'post_type', 'title', 'content']
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Required fields: {required_fields}"}), 400
        
        # Create message for community agent
        message = AgentMessage(
            id=f"post_{datetime.now().timestamp()}",
            sender="api",
            recipient="community",
            message_type="create_post",
            content=data,
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(community.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "post": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to create post"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/community/feed', methods=['GET'])
def get_community_feed():
    """Get personalized community feed"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        feed_type = request.args.get('feed_type', 'recommended')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('post_type'):
            filters['post_type'] = request.args.get('post_type')
        if request.args.get('tags'):
            filters['tags'] = request.args.get('tags').split(',')
        
        # Create message for community agent
        message = AgentMessage(
            id=f"feed_{datetime.now().timestamp()}",
            sender="api",
            recipient="community",
            message_type="get_community_feed",
            content={
                "user_id": user_id,
                "feed_type": feed_type,
                "filters": filters,
                "limit": limit,
                "offset": offset
            },
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(community.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "feed": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to get community feed"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/workflow/<workflow_name>', methods=['POST'])
def execute_workflow(workflow_name):
    """Execute a predefined workflow"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        user_id = data.get('user_id', 'anonymous')
        
        # Execute workflow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            workflow_result = loop.run_until_complete(
                orchestrator.execute_workflow(workflow_name, data, user_id)
            )
            
            return jsonify({
                "success": True,
                "workflow_result": {
                    "workflow_id": workflow_result["workflow_id"],
                    "status": workflow_result["status"],
                    "results": workflow_result["results"],
                    "execution_time": (
                        workflow_result.get("end_time", datetime.now()) - 
                        workflow_result["start_time"]
                    ).total_seconds() if "end_time" in workflow_result else None
                },
                "timestamp": datetime.now().isoformat()
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/agents/status', methods=['GET'])
def get_agents_status():
    """Get status of all agents"""
    try:
        agent_id = request.args.get('agent_id')
        status = orchestrator.get_agent_status(agent_id)
        
        return jsonify({
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/workflows/status', methods=['GET'])
def get_workflows_status():
    """Get status of workflows"""
    try:
        workflow_id = request.args.get('workflow_id')
        status = orchestrator.get_workflow_status(workflow_id)
        
        return jsonify({
            "success": True,
            "workflows": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/metrics', methods=['GET'])
def get_system_metrics():
    """Get system performance metrics"""
    try:
        metrics = orchestrator.get_metrics()
        
        return jsonify({
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/equity-calculator', methods=['POST'])
def calculate_equity():
    """Calculate hand equity and pot odds"""
    try:
        data = request.get_json()
        
        required_fields = ['hero_cards', 'board']
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Required fields: {required_fields}"}), 400
        
        # Create message for hand analyzer
        message = AgentMessage(
            id=f"equity_{datetime.now().timestamp()}",
            sender="api",
            recipient="hand_analyzer",
            message_type="calculate_equity",
            content=data,
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(hand_analyzer.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "equity_calculation": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to calculate equity"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/identify-leaks', methods=['POST'])
def identify_leaks():
    """Identify poker leaks from hand histories"""
    try:
        data = request.get_json()
        
        if not data or 'hand_histories' not in data:
            return jsonify({"error": "hand_histories is required"}), 400
        
        # Create message for hand analyzer
        message = AgentMessage(
            id=f"leaks_{datetime.now().timestamp()}",
            sender="api",
            recipient="hand_analyzer",
            message_type="identify_leaks",
            content=data,
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(hand_analyzer.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "leak_analysis": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to identify leaks"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/encouragement', methods=['POST'])
def get_encouragement():
    """Get motivational coaching and encouragement"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({"error": "user_id is required"}), 400
        
        # Create message for coach
        message = AgentMessage(
            id=f"encouragement_{datetime.now().timestamp()}",
            sender="api",
            recipient="coach",
            message_type="provide_encouragement",
            content=data,
            timestamp=datetime.now(),
            requires_response=True
        )
        
        # Process message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(coach.process_message(message))
            
            if response and response.content:
                return jsonify({
                    "success": True,
                    "encouragement": response.content,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"error": "Failed to get encouragement"}), 500
                
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error handlers
@agents_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@agents_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@agents_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

