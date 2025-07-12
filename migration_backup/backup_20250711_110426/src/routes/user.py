from flask import Blueprint

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/api/health')
def health_check():
    return { "status": "ok" }

