"""
Dashboard Routes - KPIs and Overview
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Item, Category, Lot, Batch, Sale, Transaction
from datetime import datetime, date, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/kpis', methods=['GET'])
@jwt_required()
def get_kpis():
    """Get dashboard KPIs"""
    today = date.today()
    
    # Total Items
    total_items = Item.query.count()
    
    # Total Categories
    total_categories = Category.query.count()
    
    # Total Quantity
    total_quantity = db.session.query(func.sum(Item.quantity)).scalar() or 0
    
    # Low Stock Alerts (items below reorder level)
    low_stock_items = Item.query.filter(
        Item.quantity <= Item.reorder_level
    ).all()
    low_stock_count = len(low_stock_items)
    
    # Expiring Soon (within 7 days)
    expiry_threshold = today + timedelta(days=7)
    expiring_soon_lots = Lot.query.filter(
        Lot.expiration_date <= expiry_threshold,
        Lot.expiration_date >= today,
        Lot.remaining_quantity > 0
    ).all()
    expiring_soon_count = len(expiring_soon_lots)
    
    # Expired items
    expired_lots = Lot.query.filter(
        Lot.expiration_date < today,
        Lot.remaining_quantity > 0
    ).all()
    expired_count = len(expired_lots)
    
    # Today's sales
    today_sales = db.session.query(
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_price).label('total')
    ).filter(func.date(Sale.date) == today).first()
    
    return jsonify({
        'total_items': total_items,
        'total_categories': total_categories,
        'total_quantity': total_quantity,
        'low_stock_alerts': low_stock_count,
        'expiring_soon': expiring_soon_count,
        'expired': expired_count,
        'today_sales_count': today_sales.count or 0,
        'today_sales_total': float(today_sales.total or 0)
    }), 200

@dashboard_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get all alerts for Action Center"""
    alerts = []
    today = date.today()
    
    # Low stock alerts
    low_stock_items = Item.query.filter(
        Item.quantity <= Item.reorder_level
    ).all()
    for item in low_stock_items:
        alerts.append({
            'type': 'low_stock',
            'severity': 'warning',
            'title': 'Low Stock Alert',
            'message': f'{item.name} (SKU: {item.sku}) - {item.quantity} {item.unit} remaining (Reorder: {item.reorder_level})',
            'item_id': item.id,
            'created_at': datetime.now().isoformat()
        })
    
    # Expiring soon alerts
    expiry_threshold = today + timedelta(days=7)
    expiring_soon_lots = Lot.query.filter(
        Lot.expiration_date <= expiry_threshold,
        Lot.expiration_date >= today,
        Lot.remaining_quantity > 0
    ).all()
    for lot in expiring_soon_lots:
        days_left = (lot.expiration_date - today).days
        alerts.append({
            'type': 'expiring_soon',
            'severity': 'warning',
            'title': 'Expiring Soon',
            'message': f'{lot.item.name} (Lot: {lot.lot_number}) - Expires in {days_left} days',
            'item_id': lot.item_id,
            'lot_id': lot.id,
            'created_at': datetime.now().isoformat()
        })
    
    # Expired alerts
    expired_lots = Lot.query.filter(
        Lot.expiration_date < today,
        Lot.remaining_quantity > 0
    ).all()
    for lot in expired_lots:
        alerts.append({
            'type': 'expired',
            'severity': 'critical',
            'title': 'Expired Item',
            'message': f'{lot.item.name} (Lot: {lot.lot_number}) - Expired on {lot.expiration_date}',
            'item_id': lot.item_id,
            'lot_id': lot.id,
            'created_at': datetime.now().isoformat()
        })
    
    # Sort by severity (critical first)
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    alerts.sort(key=lambda x: severity_order.get(x['severity'], 2))
    
    return jsonify({'alerts': alerts}), 200

@dashboard_bp.route('/stock-by-category', methods=['GET'])
@jwt_required()
def get_stock_by_category():
    """Get stock levels per category for bar chart"""
    # Get stock quantity by category
    results = db.session.query(
        Category.name,
        func.sum(Item.quantity).label('total_quantity'),
        func.count(Item.id).label('item_count')
    ).join(Item, Item.category_id == Category.id
    ).group_by(Category.id, Category.name).all()
    
    categories = []
    quantities = []
    item_counts = []
    
    for row in results:
        categories.append(row.name)
        quantities.append(float(row.total_quantity or 0))
        item_counts.append(row.item_count)
    
    return jsonify({
        'categories': categories,
        'quantities': quantities,
        'item_counts': item_counts
    }), 200

@dashboard_bp.route('/recent-transactions', methods=['GET'])
@jwt_required()
def get_recent_transactions():
    """Get recent transactions"""
    limit = request.args.get('limit', 10, type=int)
    
    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions]
    }), 200

@dashboard_bp.route('/expiry-overview', methods=['GET'])
@jwt_required()
def get_expiry_overview():
    """Get expiration risk overview"""
    today = date.today()
    
    # Safe items (more than 7 days until expiry)
    safe_count = Lot.query.filter(
        Lot.expiration_date > today + timedelta(days=7),
        Lot.remaining_quantity > 0
    ).count()
    
    # Expiring soon (within 7 days)
    expiring_soon_count = Lot.query.filter(
        Lot.expiration_date <= today + timedelta(days=7),
        Lot.expiration_date >= today,
        Lot.remaining_quantity > 0
    ).count()
    
    # Expired
    expired_count = Lot.query.filter(
        Lot.expiration_date < today,
        Lot.remaining_quantity > 0
    ).count()
    
    return jsonify({
        'safe': safe_count,
        'expiring_soon': expiring_soon_count,
        'expired': expired_count
    }), 200

@dashboard_bp.route('/sales-trend', methods=['GET'])
@jwt_required()
def get_sales_trend():
    """Get sales trend for last N days"""
    days = request.args.get('days', 30, type=int)
    
    start_date = date.today() - timedelta(days=days)
    
    results = db.session.query(
        func.date(Sale.date).label('date'),
        func.count(Sale.id).label('count'),
        func.sum(Sale.quantity).label('quantity'),
        func.sum(Sale.total_price).label('revenue')
    ).filter(
        func.date(Sale.date) >= start_date
    ).group_by(
        func.date(Sale.date)
    ).order_by(
        func.date(Sale.date)
    ).all()
    
    dates = []
    quantities = []
    revenues = []
    
    for row in results:
        dates.append(row.date.isoformat())
        quantities.append(row.quantity or 0)
        revenues.append(float(row.revenue or 0))
    
    return jsonify({
        'dates': dates,
        'quantities': quantities,
        'revenues': revenues
    }), 200
