from flask import Blueprint, request, jsonify
from src.harmony_engine import HarmonyEngine

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        message = data.get("message", "")
        context = data.get("context", {})
        response = HarmonyEngine.respond(user_id, message, context)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
