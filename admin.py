"""
Admin Routes - User Management and Admin Panel
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, ActivityLog, Item, Transaction
import bcrypt

admin_bp = Blueprint('admin', __name__)

def require_admin():
    """Check if current user is admin"""
    identity = get_jwt_identity()
    if identity['role'] not in ['admin', 'owner']:
        return jsonify({'error': 'Admin access required'}), 403
    return None

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [user.to_dict() for user in users]}), 200

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create new user (admin only)"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    identity = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Validate role
    if data['role'] not in ['admin', 'employee', 'owner']:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Hash password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password.decode('utf-8'),
        role=data['role'],
        status='active'
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='User created',
        details=f'Created user: {user.name} ({user.role})'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    identity = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        # Check if new email already exists
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email already exists'}), 400
        user.email = data['email']
    if 'role' in data:
        if data['role'] not in ['admin', 'employee', 'owner']:
            return jsonify({'error': 'Invalid role'}), 400
        user.role = data['role']
    if 'status' in data:
        if data['status'] not in ['active', 'inactive']:
            return jsonify({'error': 'Invalid status'}), 400
        user.status = data['status']
    if 'password' in data:
        # Hash new password
        user.password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='User updated',
        details=f'Updated user: {user.name} (ID: {user.id})'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def deactivate_user(user_id):
    """Deactivate user"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    identity = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Cannot deactivate self
    if user.id == identity['id']:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    user.status = 'inactive'
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='User deactivated',
        details=f'Deactivated user: {user.name} (ID: {user.id})'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'User deactivated successfully'}), 200

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@jwt_required()
def activate_user(user_id):
    """Activate user"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    identity = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.status = 'active'
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='User activated',
        details=f'Activated user: {user.name} (ID: {user.id})'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'User activated successfully',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/activity-logs', methods=['GET'])
@jwt_required()
def get_activity_logs():
    """Get activity logs"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    # Query parameters
    limit = request.args.get('limit', 50, type=int)
    user_id = request.args.get('user_id')
    
    query = ActivityLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    }), 200

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get system statistics"""
    # Check admin access
    error = require_admin()
    if error:
        return error
    
    # User stats
    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()
    inactive_users = User.query.filter_by(status='inactive').count()
    
    # Role distribution
    admin_count = User.query.filter_by(role='admin').count()
    employee_count = User.query.filter_by(role='employee').count()
    owner_count = User.query.filter_by(role='owner').count()
    
    # Transaction stats
    from datetime import datetime, timedelta
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    today_transactions = Transaction.query.filter(
        Transaction.created_at >= today_start
    ).count()
    
    total_transactions = Transaction.query.count()
    
    # Item stats
    total_items = Item.query.count()
    low_stock_items = Item.query.filter(Item.quantity <= Item.reorder_level).count()
    
    return jsonify({
        'users': {
            'total': total_users,
            'active': active_users,
            'inactive': inactive_users,
            'by_role': {
                'admin': admin_count,
                'employee': employee_count,
                'owner': owner_count
            }
        },
        'transactions': {
            'today': today_transactions,
            'total': total_transactions
        },
        'items': {
            'total': total_items,
            'low_stock': low_stock_items
        }
    }), 200
