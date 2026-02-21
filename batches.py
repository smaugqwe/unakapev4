"""
Batch Management Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Batch, Item, Transaction, ActivityLog
from datetime import datetime
import uuid

batches_bp = Blueprint('batches', __name__)

def generate_batch_number():
    """Generate unique batch number"""
    return f"BATCH-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

@batches_bp.route('', methods=['GET'])
@jwt_required()
def get_batches():
    """Get all batches"""
    item_id = request.args.get('item_id')
    status = request.args.get('status')
    
    query = Batch.query
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    
    if status:
        query = query.filter_by(status=status)
    
    batches = query.order_by(Batch.production_date.desc()).all()
    return jsonify({'batches': [batch.to_dict() for batch in batches]}), 200

@batches_bp.route('/<int:batch_id>', methods=['GET'])
@jwt_required()
def get_batch(batch_id):
    """Get single batch"""
    batch = Batch.query.get(batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    return jsonify({'batch': batch.to_dict()}), 200

@batches_bp.route('', methods=['POST'])
@jwt_required()
def create_batch():
    """Create new batch"""
    identity = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['item_id', 'production_date', 'quantity']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if item exists
    item = Item.query.get(data['item_id'])
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Generate batch number
    batch_number = data.get('batch_number') or generate_batch_number()
    
    # Check if batch number already exists
    if Batch.query.filter_by(batch_number=batch_number).first():
        return jsonify({'error': 'Batch number already exists'}), 400
    
    # Parse production date
    try:
        production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Create batch
    quantity = int(data['quantity'])
    batch = Batch(
        item_id=data['item_id'],
        batch_number=batch_number,
        production_date=production_date,
        quantity=quantity,
        remaining_quantity=quantity,
        status='active'
    )
    
    db.session.add(batch)
    
    # Update item quantity
    item.quantity += quantity
    
    # Log transaction
    transaction = Transaction(
        user_id=identity['id'],
        action='ADD',
        item_id=item.id,
        reference_id=batch.id,
        reference_type='batch',
        quantity=quantity,
        details=f'Added batch {batch_number}: {quantity} {item.unit}'
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Batch created',
        details=f'Created batch {batch_number} for item {item.name}'
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Batch created successfully',
        'batch': batch.to_dict()
    }), 201

@batches_bp.route('/<int:batch_id>', methods=['PUT'])
@jwt_required()
def update_batch(batch_id):
    """Update batch"""
    identity = get_jwt_identity()
    batch = Batch.query.get(batch_id)
    
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    data = request.get_json()
    
    if 'production_date' in data:
        try:
            batch.production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    if 'quantity' in data:
        old_quantity = batch.remaining_quantity
        batch.quantity = data['quantity']
        batch.remaining_quantity = data['quantity']
        
        # Update item quantity
        item = batch.item
        item.quantity += (batch.remaining_quantity - old_quantity)
    
    if 'status' in data:
        batch.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Batch updated successfully',
        'batch': batch.to_dict()
    }), 200

@batches_bp.route('/<int:batch_id>', methods=['DELETE'])
@jwt_required()
def delete_batch(batch_id):
    """Delete batch"""
    identity = get_jwt_identity()
    batch = Batch.query.get(batch_id)
    
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Check if batch has sales
    if batch.sales:
        return jsonify({'error': 'Cannot delete batch with sales'}), 400
    
    # Update item quantity
    item = batch.item
    item.quantity -= batch.remaining_quantity
    
    # Log transaction
    transaction = Transaction(
        user_id=identity['id'],
        action='DELETE',
        item_id=item.id,
        reference_id=batch.id,
        reference_type='batch',
        quantity=-batch.remaining_quantity,
        details=f'Deleted batch {batch.batch_number}'
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Batch deleted',
        details=f'Deleted batch {batch.batch_number}'
    )
    db.session.add(log)
    
    db.session.delete(batch)
    db.session.commit()
    
    return jsonify({'message': 'Batch deleted successfully'}), 200
