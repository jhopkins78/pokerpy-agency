from flask import Blueprint, request, jsonify
from src.harmony_engine import HarmonyEngine

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        import os
        import json
        from datetime import datetime

        data = request.get_json(force=True)
        user_id = data.get("user_id", "anon")
        message = data.get("message", "")
        context = data.get("context", {})
        response = HarmonyEngine.respond(user_id, message, context)

        # --- Chat Log Tracking ---
        log_entry = {
            "user_id": user_id,
            "message": message,
            "context": context,
            "response": response.get("response"),
            "sources": [
                {
                    "title": s.get("title", ""),
                    "url": s.get("url", "")
                } for s in response.get("sources", [])
            ],
            "timestamp": datetime.now().isoformat(),
            "used_simulation": bool(response.get("suggested_simulation"))
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
