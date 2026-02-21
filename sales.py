"""
Sales Management Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Sale, Item, Batch, Lot, Transaction, ActivityLog
from datetime import datetime, date
from sqlalchemy import func

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('', methods=['GET'])
@jwt_required()
def get_sales():
    """Get all sales"""
    item_id = request.args.get('item_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Sale.query
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Sale.date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Sale.date <= end)
        except ValueError:
            pass
    
    sales = query.order_by(Sale.date.desc()).all()
    return jsonify({'sales': [sale.to_dict() for sale in sales]}), 200

@sales_bp.route('/<int:sale_id>', methods=['GET'])
@jwt_required()
def get_sale(sale_id):
    """Get single sale"""
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    
    return jsonify({'sale': sale.to_dict()}), 200

@sales_bp.route('', methods=['POST'])
@jwt_required()
def create_sale():
    """Create new sale"""
    identity = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if not data.get('item_id') or not data.get('quantity'):
        return jsonify({'error': 'item_id and quantity are required'}), 400
    
    # Check if item exists
    item = Item.query.get(data['item_id'])
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    quantity = int(data['quantity'])
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    # Check if sufficient stock
    if item.quantity < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    batch_id = data.get('batch_id')
    lot_id = data.get('lot_id')
    
    # Determine which batch/lot to deduct from
    if item.is_perishable and lot_id:
        # Use lot tracking for perishables
        lot = Lot.query.get(lot_id)
        if not lot:
            return jsonify({'error': 'Lot not found'}), 404
        
        # Check if lot is expired
        if lot.expiration_date and lot.expiration_date < date.today():
            return jsonify({'error': 'Cannot sell expired lot'}), 400
        
        # Check if lot has sufficient quantity
        if lot.remaining_quantity < quantity:
            return jsonify({'error': 'Insufficient quantity in lot'}), 400
        
        # Deduct from lot
        lot.remaining_quantity -= quantity
        if lot.remaining_quantity <= 0:
            lot.status = 'consumed'
        
        reference_type = 'lot'
        reference_id = lot.id
        reference_number = lot.lot_number
        
    elif batch_id:
        # Use batch tracking
        batch = Batch.query.get(batch_id)
        if not batch:
            return jsonify({'error': 'Batch not found'}), 404
        
        # Check if batch has sufficient quantity
        if batch.remaining_quantity < quantity:
            return jsonify({'error': 'Insufficient quantity in batch'}), 400
        
        # Deduct from batch
        batch.remaining_quantity -= quantity
        if batch.remaining_quantity <= 0:
            batch.status = 'consumed'
        
        reference_type = 'batch'
        reference_id = batch.id
        reference_number = batch.batch_number
        
    else:
        # General deduction from item quantity
        reference_type = None
        reference_id = None
        reference_number = None
        
        # Find oldest active lot first for perishables
        if item.is_perishable:
            lot = Lot.query.filter(
                Lot.item_id == item.id,
                Lot.remaining_quantity > 0,
                Lot.expiration_date >= date.today()
            ).order_by(Lot.expiration_date.asc()).first()
            
            if lot:
                if lot.remaining_quantity >= quantity:
                    lot.remaining_quantity -= quantity
                    if lot.remaining_quantity <= 0:
                        lot.status = 'consumed'
                    reference_type = 'lot'
                    reference_id = lot.id
                    reference_number = lot.lot_number
                else:
                    # Partial deduction from lot, rest from item
                    remaining_qty = quantity
                    qty_from_lot = lot.remaining_quantity
                    lot.remaining_quantity = 0
                    lot.status = 'consumed'
                    
                    # Find more lots if needed
                    qty_from_item = remaining_qty - qty_from_lot
                    if qty_from_item > 0:
                        item.quantity -= qty_from_item
                    
                    reference_type = 'lot'
                    reference_id = lot.id
                    reference_number = lot.lot_number
        
        # If not from lot, deduct from item directly
        if not reference_type:
            item.quantity -= quantity
    
    # Update item quantity if not already done
    if not (item.is_perishable and lot_id):
        item.quantity -= quantity
    
    # Calculate price
    unit_price = float(data.get('unit_price', 0))
    total_price = unit_price * quantity
    
    # Create sale record
    sale = Sale(
        item_id=item.id,
        batch_id=batch_id if not item.is_perishable else None,
        lot_id=lot_id if item.is_perishable else None,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        sold_by=identity['id'],
        customer_name=data.get('customer_name'),
        notes=data.get('notes')
    )
    
    db.session.add(sale)
    
    # Log transaction
    transaction = Transaction(
        user_id=identity['id'],
        action='SALE',
        item_id=item.id,
        reference_id=sale.id,
        reference_type='sale',
        quantity=-quantity,
        details=f'Sold {quantity} {item.unit} of {item.name}' + 
               (f' from {reference_number}' if reference_number else '')
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Sale created',
        details=f'Sold {quantity} {item.unit} of {item.name} for ${total_price}'
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Sale created successfully',
        'sale': sale.to_dict()
    }), 201

@sales_bp.route('/<int:sale_id>', methods=['DELETE'])
@jwt_required()
def delete_sale(sale_id):
    """Delete/cancel sale"""
    identity = get_jwt_identity()
    sale = Sale.query.get(sale_id)
    
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    
    # Restore quantity to item
    item = sale.item
    item.quantity += sale.quantity
    
    # Restore batch/lot quantity if applicable
    if sale.batch:
        sale.batch.remaining_quantity += sale.quantity
        if sale.batch.remaining_quantity > 0:
            sale.batch.status = 'active'
    
    if sale.lot:
        sale.lot.remaining_quantity += sale.quantity
        if sale.lot.remaining_quantity > 0:
            sale.lot.status = 'active'
    
    # Log transaction
    transaction = Transaction(
        user_id=identity['id'],
        action='SALE_CANCEL',
        item_id=item.id,
        reference_id=sale.id,
        reference_type='sale',
        quantity=sale.quantity,
        details=f'Cancelled sale of {sale.quantity} {item.unit}'
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Sale cancelled',
        details=f'Cancelled sale ID {sale.id}'
    )
    db.session.add(log)
    
    db.session.delete(sale)
    db.session.commit()
    
    return jsonify({'message': 'Sale cancelled successfully'}), 200

@sales_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_sales_summary():
    """Get sales summary"""
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Today's sales
    today_sales = db.session.query(
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_price).label('total')
    ).filter(func.date(Sale.date) == today).first()
    
    # This month's sales
    month_sales = db.session.query(
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_price).label('total')
    ).filter(Sale.date >= start_of_month).first()
    
    # Total sales
    total_sales = db.session.query(
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_price).label('total')
    ).first()
    
    return jsonify({
        'today': {
            'count': today_sales.count or 0,
            'total': float(today_sales.total or 0)
        },
        'this_month': {
            'count': month_sales.count or 0,
            'total': float(month_sales.total or 0)
        },
        'total': {
            'count': total_sales.count or 0,
            'total': float(total_sales.total or 0)
        }
    }), 200
