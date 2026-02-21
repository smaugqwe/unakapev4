"""
Item Management Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Item, Category, Supplier, Transaction, ActivityLog
from datetime import datetime

items_bp = Blueprint('items', __name__)

@items_bp.route('', methods=['GET'])
@jwt_required()
def get_items():
    """Get all items"""
    # Query parameters
    category_id = request.args.get('category_id')
    search = request.args.get('search')
    low_stock = request.args.get('low_stock')
    
    query = Item.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            db.or_(
                Item.name.ilike(f'%{search}%'),
                Item.sku.ilike(f'%{search}%')
            )
        )
    
    if low_stock == 'true':
        query = query.filter(Item.quantity <= Item.reorder_level)
    
    items = query.order_by(Item.name).all()
    return jsonify({'items': [item.to_dict() for item in items]}), 200

@items_bp.route('/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    """Get single item"""
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    return jsonify({'item': item.to_dict()}), 200

@items_bp.route('', methods=['POST'])
@jwt_required()
def create_item():
    """Create new item"""
    identity = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'sku', 'category_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if SKU already exists
    if Item.query.filter_by(sku=data['sku']).first():
        return jsonify({'error': 'SKU already exists'}), 400
    
    # Check if category exists
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    # Create item
    item = Item(
        name=data['name'],
        category_id=data['category_id'],
        sku=data['sku'],
        quantity=data.get('quantity', 0),
        unit=data.get('unit', 'pcs'),
        reorder_level=data.get('reorder_level', 10),
        supplier_id=data.get('supplier_id'),
        description=data.get('description'),
        is_perishable=data.get('is_perishable', False)
    )
    
    db.session.add(item)
    db.session.commit()
    
    # Log transaction
    if item.quantity > 0:
        transaction = Transaction(
            user_id=identity['id'],
            action='ADD',
            item_id=item.id,
            quantity=item.quantity,
            details=f'Initial stock: {item.quantity} {item.unit}'
        )
        db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Item created',
        details=f'Created item: {item.name} (SKU: {item.sku})'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Item created successfully',
        'item': item.to_dict()
    }), 201

@items_bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    """Update item"""
    identity = get_jwt_identity()
    item = Item.query.get(item_id)
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    data = request.get_json()
    old_quantity = item.quantity
    
    # Update fields
    if 'name' in data:
        item.name = data['name']
    if 'category_id' in data:
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        item.category_id = data['category_id']
    if 'sku' in data:
        # Check if new SKU already exists
        existing = Item.query.filter_by(sku=data['sku']).first()
        if existing and existing.id != item_id:
            return jsonify({'error': 'SKU already exists'}), 400
        item.sku = data['sku']
    if 'quantity' in data:
        item.quantity = data['quantity']
    if 'unit' in data:
        item.unit = data['unit']
    if 'reorder_level' in data:
        item.reorder_level = data['reorder_level']
    if 'supplier_id' in data:
        item.supplier_id = data['supplier_id']
    if 'description' in data:
        item.description = data['description']
    if 'is_perishable' in data:
        item.is_perishable = data['is_perishable']
    
    db.session.commit()
    
    # Log transaction if quantity changed
    if item.quantity != old_quantity:
        transaction = Transaction(
            user_id=identity['id'],
            action='UPDATE',
            item_id=item.id,
            quantity=item.quantity - old_quantity,
            details=f'Quantity updated from {old_quantity} to {item.quantity}'
        )
        db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Item updated',
        details=f'Updated item: {item.name} (ID: {item.id})'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Item updated successfully',
        'item': item.to_dict()
    }), 200

@items_bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    """Delete item"""
    identity = get_jwt_identity()
    item = Item.query.get(item_id)
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Log transaction before deletion
    transaction = Transaction(
        user_id=identity['id'],
        action='DELETE',
        item_id=item.id,
        quantity=item.quantity,
        details=f'Deleted item: {item.name} (SKU: {item.sku})'
    )
    db.session.add(transaction)
    
    # Log activity
    log = ActivityLog(
        user_id=identity['id'],
        action='Item deleted',
        details=f'Deleted item: {item.name} (SKU: {item.sku})'
    )
    db.session.add(log)
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted successfully'}), 200

# Category routes
@items_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all categories"""
    categories = Category.query.order_by(Category.name).all()
    return jsonify({'categories': [cat.to_dict() for cat in categories]}), 200

@items_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Create new category"""
    identity = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400
    
    # Check if category already exists
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Category already exists'}), 400
    
    category = Category(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'message': 'Category created successfully',
        'category': category.to_dict()
    }), 201

@items_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get(category_id)
    
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    # Check if category has items
    if Item.query.filter_by(category_id=category_id).first():
        return jsonify({'error': 'Cannot delete category with items'}), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Category deleted successfully'}), 200

# Supplier routes
@items_bp.route('/suppliers', methods=['GET'])
@jwt_required()
def get_suppliers():
    """Get all suppliers"""
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify({'suppliers': [sup.to_dict() for sup in suppliers]}), 200

@items_bp.route('/suppliers', methods=['POST'])
@jwt_required()
def create_supplier():
    """Create new supplier"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Supplier name is required'}), 400
    
    supplier = Supplier(
        name=data['name'],
        contact=data.get('contact'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address')
    )
    
    db.session.add(supplier)
    db.session.commit()
    
    return jsonify({
        'message': 'Supplier created successfully',
        'supplier': supplier.to_dict()
    }), 201

@items_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    """Delete supplier"""
    supplier = Supplier.query.get(supplier_id)
    
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404
    
    # Check if supplier has items
    if Item.query.filter_by(supplier_id=supplier_id).first():
        return jsonify({'error': 'Cannot delete supplier with items'}), 400
    
    db.session.delete(supplier)
    db.session.commit()
    
    return jsonify({'message': 'Supplier deleted successfully'}), 200
