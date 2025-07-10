"""
Authentication routes for PokerPy
Handles user registration, login, and JWT token management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, 
    create_refresh_token, get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import re

from src.models.poker_models import db, User, UserReputation, SkillLevel

auth_bp = Blueprint('auth', __name__)

# JWT blacklist for logout functionality
blacklisted_tokens = set()

def init_jwt(app):
    """Initialize JWT manager"""
    jwt = JWTManager(app)
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload['jti'] in blacklisted_tokens
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401
    
    return jwt

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate input
        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': 'Username must be between 3 and 50 characters'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid, password_message = validate_password(password)
        if not is_valid:
            return jsonify({'error': password_message}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        new_user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            skill_level=SkillLevel(data.get('skill_level', 'beginner')),
            preferred_game=data.get('preferred_game', "No Limit Hold'em"),
            coaching_style=data.get('coaching_style', 'encouraging'),
            explanation_style=data.get('explanation_style', 'simple'),
            learning_pace=data.get('learning_pace', 'moderate'),
            created_at=datetime.utcnow()
        )
        
        # Create user reputation
        user_reputation = UserReputation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            reputation_score=0,
            level="newbie"
        )
        
        # Save to database
        db.session.add(new_user)
        db.session.add(user_reputation)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': new_user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        return jsonify({
            'success': True,
            'message': 'Successfully logged out'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        new_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'success': True,
            'access_token': new_token
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user reputation
        reputation = UserReputation.query.filter_by(user_id=current_user_id).first()
        
        profile_data = user.to_dict()
        if reputation:
            profile_data['reputation'] = reputation.to_dict()
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        updatable_fields = [
            'skill_level', 'preferred_game', 'coaching_style', 
            'explanation_style', 'learning_pace', 'timezone'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'skill_level':
                    try:
                        setattr(user, field, SkillLevel(data[field]))
                    except ValueError:
                        return jsonify({'error': f'Invalid skill level: {data[field]}'}), 400
                else:
                    setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verify current password
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, password_message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': password_message}), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify if token is valid"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'valid': True,
            'user_id': current_user_id,
            'username': user.username
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """Delete user account"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({'error': 'Password confirmation is required'}), 400
        
        password = data['password']
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Password is incorrect'}), 401
        
        # Delete user (cascade will handle related records)
        db.session.delete(user)
        db.session.commit()
        
        # Blacklist current token
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Error handlers
@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@auth_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

