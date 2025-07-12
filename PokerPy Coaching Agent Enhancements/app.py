from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime, timedelta
import openai
from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass, asdict
import logging

# Import custom modules
from coaching_agent import PokerCoachingAgent
from simulation_room import SimulationRoom
from goal_tracker import GoalTracker
from memory_manager import MemoryManager
from rag_system import RAGSystem

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'poker-coaching-secret-key')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
rag_system = RAGSystem()
memory_manager = MemoryManager()
coaching_agent = PokerCoachingAgent(rag_system, memory_manager)
simulation_room = SimulationRoom(coaching_agent)
goal_tracker = GoalTracker(memory_manager)

@dataclass
class ChatMessage:
    id: str
    user_id: str
    message: str
    response: str
    timestamp: datetime
    context: Dict
    
@dataclass
class UserProfile:
    user_id: str
    name: str
    skill_level: str
    goals: List[Dict]
    psychological_profile: Dict
    session_history: List[Dict]
    preferences: Dict

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint for coaching conversations"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', str(uuid.uuid4()))
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get user profile
        user_profile = memory_manager.get_user_profile(user_id)
        
        # Generate coaching response
        response = coaching_agent.generate_response(
            user_id=user_id,
            message=message,
            context=context,
            user_profile=user_profile
        )
        
        # Save conversation
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            message=message,
            response=response['message'],
            timestamp=datetime.now(),
            context=response.get('context', {})
        )
        
        memory_manager.save_conversation(chat_message)
        
        return jsonify({
            "response": response['message'],
            "context": response.get('context', {}),
            "suggestions": response.get('suggestions', []),
            "user_id": user_id
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start a poker simulation scenario"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        scenario_type = data.get('scenario_type', 'cash_game')
        difficulty = data.get('difficulty', 'beginner')
        custom_params = data.get('custom_params', {})
        
        simulation = simulation_room.create_simulation(
            user_id=user_id,
            scenario_type=scenario_type,
            difficulty=difficulty,
            custom_params=custom_params
        )
        
        return jsonify({
            "simulation_id": simulation['id'],
            "scenario": simulation['scenario'],
            "instructions": simulation['instructions'],
            "initial_state": simulation['state']
        })
        
    except Exception as e:
        logger.error(f"Simulation start error: {str(e)}")
        return jsonify({"error": "Failed to start simulation"}), 500

@app.route('/api/simulation/<simulation_id>/action', methods=['POST'])
def simulation_action(simulation_id):
    """Process an action in a simulation"""
    try:
        data = request.get_json()
        action = data.get('action')
        parameters = data.get('parameters', {})
        
        result = simulation_room.process_action(
            simulation_id=simulation_id,
            action=action,
            parameters=parameters
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Simulation action error: {str(e)}")
        return jsonify({"error": "Failed to process action"}), 500

@app.route('/api/goals', methods=['GET', 'POST'])
def handle_goals():
    """Handle goal tracking operations"""
    try:
        if request.method == 'GET':
            user_id = request.args.get('user_id')
            goals = goal_tracker.get_user_goals(user_id)
            return jsonify({"goals": goals})
            
        elif request.method == 'POST':
            data = request.get_json()
            user_id = data.get('user_id')
            goal_data = data.get('goal')
            
            goal = goal_tracker.create_goal(user_id, goal_data)
            return jsonify({"goal": goal})
            
    except Exception as e:
        logger.error(f"Goals error: {str(e)}")
        return jsonify({"error": "Failed to handle goals"}), 500

@app.route('/api/goals/<goal_id>/update', methods=['PUT'])
def update_goal(goal_id):
    """Update goal progress"""
    try:
        data = request.get_json()
        progress = data.get('progress')
        notes = data.get('notes', '')
        
        updated_goal = goal_tracker.update_progress(goal_id, progress, notes)
        return jsonify({"goal": updated_goal})
        
    except Exception as e:
        logger.error(f"Goal update error: {str(e)}")
        return jsonify({"error": "Failed to update goal"}), 500

@app.route('/api/profile', methods=['GET', 'POST'])
def handle_profile():
    """Handle user profile operations"""
    try:
        if request.method == 'GET':
            user_id = request.args.get('user_id')
            profile = memory_manager.get_user_profile(user_id)
            return jsonify({"profile": profile})
            
        elif request.method == 'POST':
            data = request.get_json()
            user_id = data.get('user_id')
            profile_data = data.get('profile')
            
            profile = memory_manager.update_user_profile(user_id, profile_data)
            return jsonify({"profile": profile})
            
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"error": "Failed to handle profile"}), 500

@app.route('/api/daily-insight', methods=['GET'])
def daily_insight():
    """Get daily motivational insight"""
    try:
        user_id = request.args.get('user_id')
        insight = coaching_agent.generate_daily_insight(user_id)
        return jsonify({"insight": insight})
        
    except Exception as e:
        logger.error(f"Daily insight error: {str(e)}")
        return jsonify({"error": "Failed to generate insight"}), 500

@app.route('/api/ask-anything', methods=['POST'])
def ask_anything():
    """Ask anything mode for life advice"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        question = data.get('question')
        category = data.get('category', 'general')
        
        response = coaching_agent.ask_anything_mode(
            user_id=user_id,
            question=question,
            category=category
        )
        
        return jsonify({"response": response})
        
    except Exception as e:
        logger.error(f"Ask anything error: {str(e)}")
        return jsonify({"error": "Failed to process question"}), 500

@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
    """Search the knowledge base"""
    try:
        data = request.get_json()
        query = data.get('query')
        category = data.get('category', 'all')
        limit = data.get('limit', 5)
        
        results = rag_system.search(query, category, limit)
        return jsonify({"results": results})
        
    except Exception as e:
        logger.error(f"Knowledge search error: {str(e)}")
        return jsonify({"error": "Failed to search knowledge"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

