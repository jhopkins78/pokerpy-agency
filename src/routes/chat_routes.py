from flask import Blueprint, request, jsonify

# Import enhanced PokerCoachingAgent and dependencies
import sys
import os
import importlib.util

# Add PokerPy Coaching Agent Enhancements to sys.path
enhancements_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../PokerPy Coaching Agent Enhancements"))
if enhancements_path not in sys.path:
    sys.path.insert(0, enhancements_path)

from coaching_agent import PokerCoachingAgent
from memory_manager import MemoryManager
from rag_system import RAGSystem

# Instantiate RAG system and memory manager
rag_system = RAGSystem()
memory_manager = MemoryManager()
agent = PokerCoachingAgent(rag_system, memory_manager)

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        import json
        from datetime import datetime

        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        message = data.get("message", "")
        context = data.get("context", {})

        # Use enhanced agent
        response = agent.generate_response(user_id, message, context)

        # --- Chat Log Tracking ---
        log_entry = {
            "user_id": user_id,
            "message": message,
            "context": context,
            "response": response.get("message"),
            "rag_debug": response.get("rag_debug"),
            "timestamp": datetime.now().isoformat(),
            "used_simulation": "Poker Simulation:" in (response.get("message") or "")
        }
        log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
        log_path = os.path.join(log_dir, "chat_log.jsonl")
        os.makedirs(log_dir, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/logs/chat', methods=['GET'])
def get_chat_logs():
    """
    Admin route to fetch chat logs for a user.
    Requires ?user_id=... and Authorization: Bearer <ADMIN_TOKEN>
    """
    import os
    import json
    from flask import current_app

    # Admin token check
    admin_token = os.environ.get("ADMIN_TOKEN", "changeme")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    token = auth_header.split(" ", 1)[1]
    if token != admin_token:
        return jsonify({"error": "Unauthorized"}), 403

    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
    log_path = os.path.join(log_dir, "chat_log.jsonl")
    if not os.path.exists(log_path):
        return jsonify({"logs": []})

    logs = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("user_id") == user_id:
                    logs.append(entry)
            except Exception:
                continue

    return jsonify({"logs": logs})
