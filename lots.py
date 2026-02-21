"""
Lot Management Routes (For Perishables)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Lot, Item, Transaction, ActivityLog
from datetime import datetime, date
import uuid

lots_bp = Blueprint('lots', __name__)

def generate_lot_number():
    """Generate unique lot number"""
    return f"LOT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def update_lot_status(lot):
    """Update lot status based on expiration date"""
    if not lot.expiration_date:
        lot.status = 'active'
        return
    
    today = date.today()
    days_until_expiry = (lot.expiration_date - today).days
    
    if lot.remaining_quantity <= 0:
        lot.status = 'consumed'
    elif days_until_expiry < 0:
        lot.status = 'expired'
    elif days_until_expiry <= 7:
        lot.status = 'expiring_soon'
    else:
        lot.status = 'active'

@lots_bp.route('', methods=['GET'])
@jwt_required()
def get_lots():
    """Get all lots"""
    item_id = request.args.get('item_id')
    status = request.args.get('status')
    expiry_filter = request.args.get('expiry_filter')  # safe, expiring_soon, expired
    
    query = Lot.query
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    
    if status:
        query = query.filter_by(status=status)
    
    lots = query.order_by(Lot.expiration_date.asc()).all()
    
    # Filter by expiry status if requested
    if expiry_filter:
        lots = [lot for lot in lots if lot.get_expiry_status() == expiry_filter]
        # Update statuses
        for lot in lots:
            update_lot_status(lot)
    
    return jsonify({'lots': [lot.to_dict() for lot in lots]}), 200

@lots_bp.route('/<int:lot_id>', methods=['GET'])
@jwt_required()
def get_lot(lot_id):
    """Get single lot"""
    lot = Lot.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'Lot not found'}), 404
    
    update_lot_status(lot)
    db.session.commit()
    
    return jsonify({'lot': lot.to_dict()}), 200

@lots_bp.route('', methods=['POST'])
@jwt_required()
def create_lot():
    """Create new lot"""
    identity = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['item_id', 'expiration_date', 'quantity']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if item exists
    item = Item.query.get(data['item_id'])
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Check if item is perishable
    if not item.is_perishable:
        return jsonify({'error': 'Item is not marked as perishable'}), 400
    
    # Generate lot number
    lot_number = data.get('lot_number') or generate_lot_number()
    
    # Check if lot number already exists
    if Lot.query.filter_by(lot_number=lot_number).first():
        return jsonify({'error': 'Lot number already exists'}), 400
    
    # Parse expiration date
    try:
        expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Create lot
    quantity = int(data['quantity'])
    lot = Lot(
        item_id=data['item_id'],
        lot_number=lot_number,
        expiration_date=expiration_date,
        quantity=quantity,
        remaining_quantity=quantity,
        status='active'
    )
    
    # Update lot status
    update_lot_status(lot)
    
    db.session.add(lot)
    
    # Update item quantity
    item.quantity += quantity
    
    # Log transaction
    transaction = Transaction(
        user_id=identity['id'],
        action='ADD',
        item_id=item.id,
        reference_id=lot.id,
        reference_type='lot',
        quantity=quantity,
        details=f'Added lot {lot_number}: {quantity} {item.unit}, expires {expiration_date}'
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Lot created',
        details=f'Created lot {lot_number} for item {item.name}, expires {expiration_date}'
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Lot created successfully',
        'lot': lot.to_dict()
    }), 201

@lots_bp.route('/<int:lot_id>', methods=['PUT'])
@jwt_required()
def update_lot(lot_id):
    """Update lot"""
    identity = get_jwt_identity()
    lot = Lot.query.get(lot_id)
    
    if not lot:
        return jsonify({'error': 'Lot not found'}), 404
    
    data = request.get_json()
    
    if 'expiration_date' in data:
        try:
            lot.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    if 'quantity' in data:
        old_quantity = lot.remaining_quantity
        lot.quantity = data['quantity']
        lot.remaining_quantity = data['quantity']
        
        # Update item quantity
        item = lot.item
        item.quantity += (lot.remaining_quantity - old_quantity)
    
    # Update lot status
    update_lot_status(lot)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Lot updated successfully',
        'lot': lot.to_dict()
    }), 200

@lots_bp.route('/<int:lot_id>', methods=['DELETE'])
@jwt_required()
def delete_lot(lot_id):
    """Delete lot"""
    identity = get_jwt_identity()
    lot = Lot.query.get(lot_id)
    
    if not lot:
        return jsonify({'error': 'Lot not found'}), 404
    
    # Check if lot has sales
    if lot.sales:
        return jsonify({'error': 'Cannot delete lot with sales'}), 400
    
    # Update item quantity
    item = lot.item
    item.quantity -= lot.remaining_quantity
    
    # Log transaction
    transaction = Transaction(
        user_id=identity['id'],
        action='DELETE',
        item_id=item.id,
        reference_id=lot.id,
        reference_type='lot',
        quantity=-lot.remaining_quantity,
        details=f'Deleted lot {lot.lot_number}'
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Lot deleted',
        details=f'Deleted lot {lot.lot_number}'
    )
    db.session.add(log)
    
    db.session.delete(lot)
    db.session.commit()
    
    return jsonify({'message': 'Lot deleted successfully'}), 200

@lots_bp.route('/expiring', methods=['GET'])
@jwt_required()
def get_expiring_lots():
    """Get lots expiring soon (within 7 days)"""
    today = date.today()
    from datetime import timedelta
    expiry_threshold = today + timedelta(days=7)
    
    lots = Lot.query.filter(
        Lot.expiration_date <= expiry_threshold,
        Lot.expiration_date >= today,
        Lot.remaining_quantity > 0
    ).order_by(Lot.expiration_date.asc()).all()
    
    # Update statuses
    for lot in lots:
        update_lot_status(lot)
    
    db.session.commit()
    
    return jsonify({'lots': [lot.to_dict() for lot in lots]}), 200

@lots_bp.route('/expired', methods=['GET'])
@jwt_required()
def get_expired_lots():
    """Get expired lots"""
    today = date.today()
    
    lots = Lot.query.filter(
        Lot.expiration_date < today,
        Lot.remaining_quantity > 0
    ).order_by(Lot.expiration_date.asc()).all()
    
    # Update statuses
    for lot in lots:
        update_lot_status(lot)
        lot.status = 'expired'
    
    db.session.commit()
    
    return jsonify({'lots': [lot.to_dict() for lot in lots]}), 200
