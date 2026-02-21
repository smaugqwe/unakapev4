"""
Authentication Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from models import User, ActivityLog
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Hash password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Create new user
    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password.decode('utf-8'),
        role=data.get('role', 'employee'),
        status='active'
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action='User registered',
        details=f'New user registered: {user.email}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Check password
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Check if user is active
    if user.status != 'active':
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Create access token
    access_token = create_access_token(identity={
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'name': user.name
    })
    
    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action='User logged in',
        details=f'User logged in: {user.email}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    identity = get_jwt_identity()
    user = User.query.get(identity['id'])
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    identity = get_jwt_identity()
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='User logged out',
        details=f'User logged out: {identity["email"]}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Logout successful'}), 200
