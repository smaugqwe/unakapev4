"""
Reports Routes
"""

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Item, Category, Sale, Lot, Transaction, ForecastData
from datetime import datetime, date, timedelta
from sqlalchemy import func
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/inventory', methods=['GET'])
@jwt_required()
def inventory_report():
    """Generate daily inventory report"""
    # Get date filter
    report_date = request.args.get('date')
    if report_date:
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()
    else:
        report_date = date.today()
    
    # Get all items with their current stock
    items = Item.query.all()
    
    report_data = []
    total_value = 0
    
    for item in items:
        report_data.append({
            'sku': item.sku,
            'name': item.name,
            'category': item.category.name if item.category else 'N/A',
            'quantity': item.quantity,
            'unit': item.unit,
            'reorder_level': item.reorder_level,
            'status': 'Low Stock' if item.quantity <= item.reorder_level else 'OK',
            'supplier': item.supplier.name if item.supplier else 'N/A'
        })
    
    return jsonify({
        'report_date': report_date.isoformat(),
        'total_items': len(items),
        'total_quantity': sum(item.quantity for item in items),
        'low_stock_count': sum(1 for item in items if item.quantity <= item.reorder_level),
        'data': report_data
    }), 200

@reports_bp.route('/sales', methods=['GET'])
@jwt_required()
def sales_report():
    """Generate sales report"""
    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get sales in date range
    sales = Sale.query.filter(
        func.date(Sale.date) >= start_date,
        func.date(Sale.date) <= end_date
    ).order_by(Sale.date.desc()).all()
    
    report_data = []
    total_revenue = 0
    total_quantity = 0
    
    for sale in sales:
        report_data.append({
            'date': sale.date.isoformat() if sale.date else None,
            'item': sale.item.name if sale.item else 'N/A',
            'quantity': sale.quantity,
            'unit_price': sale.unit_price,
            'total_price': sale.total_price,
            'customer': sale.customer_name or 'Walk-in',
            'sold_by': sale.sold_by_user.name if sale.sold_by_user else 'N/A'
        })
        total_revenue += sale.total_price
        total_quantity += sale.quantity
    
    return jsonify({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_transactions': len(sales),
        'total_quantity_sold': total_quantity,
        'total_revenue': total_revenue,
        'data': report_data
    }), 200

@reports_bp.route('/expiry', methods=['GET'])
@jwt_required()
def expiry_report():
    """Generate expiry report"""
    today = date.today()
    
    # Get all lots with their expiry status
    lots = Lot.query.filter(
        Lot.remaining_quantity > 0
    ).order_by(Lot.expiration_date.asc()).all()
    
    report_data = []
    expired_count = 0
    expiring_soon_count = 0
    
    for lot in lots:
        days_until_expiry = (lot.expiration_date - today).days
        
        status = 'Safe'
        if days_until_expiry < 0:
            status = 'Expired'
            expired_count += 1
        elif days_until_expiry <= 7:
            status = 'Expiring Soon'
            expiring_soon_count += 1
        
        report_data.append({
            'lot_number': lot.lot_number,
            'item': lot.item.name if lot.item else 'N/A',
            'quantity': lot.remaining_quantity,
            'expiration_date': lot.expiration_date.isoformat(),
            'days_until_expiry': days_until_expiry,
            'status': status
        })
    
    return jsonify({
        'report_date': today.isoformat(),
        'total_lots': len(lots),
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
        'data': report_data
    }), 200

@reports_bp.route('/forecast', methods=['GET'])
@jwt_required()
def forecast_report():
    """Generate forecast report"""
    item_id = request.args.get('item_id')
    
    if item_id:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Get forecast data for specific item
        forecasts = ForecastData.query.filter_by(
            item_id=item_id
        ).order_by(ForecastData.month).all()
        
        return jsonify({
            'item': item.to_dict(),
            'forecasts': [f.to_dict() for f in forecasts]
        }), 200
    
    # Get all items with forecasts
    items_with_forecasts = db.session.query(
        ForecastData.item_id,
        Item.name,
        Item.sku
    ).join(Item, Item.id == ForecastData.item_id
    ).group_by(ForecastData.item_id).all()
    
    result = []
    for item in items_with_forecasts:
        latest_forecast = ForecastData.query.filter_by(
            item_id=item.item_id
        ).order_by(ForecastData.month.desc()).first()
        
        result.append({
            'item_id': item.item_id,
            'name': item.name,
            'sku': item.sku,
            'latest_forecast': latest_forecast.to_dict() if latest_forecast else None
        })
    
    return jsonify({'items': result}), 200

@reports_bp.route('/export/inventory/csv', methods=['GET'])
@jwt_required()
def export_inventory_csv():
    """Export inventory report as CSV"""
    items = Item.query.all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['SKU', 'Name', 'Category', 'Quantity', 'Unit', 'Reorder Level', 'Status', 'Supplier'])
    
    # Data
    for item in items:
        status = 'Low Stock' if item.quantity <= item.reorder_level else 'OK'
        writer.writerow([
            item.sku,
            item.name,
            item.category.name if item.category else 'N/A',
            item.quantity,
            item.unit,
            item.reorder_level,
            status,
            item.supplier.name if item.supplier else 'N/A'
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=inventory_report_{date.today()}.csv'
    
    return response

@reports_bp.route('/export/sales/csv', methods=['GET'])
@jwt_required()
def export_sales_csv():
    """Export sales report as CSV"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    
    sales = Sale.query.filter(
        func.date(Sale.date) >= start_date,
        func.date(Sale.date) <= end_date
    ).order_by(Sale.date.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Date', 'Item', 'Quantity', 'Unit Price', 'Total Price', 'Customer', 'Sold By'])
    
    # Data
    for sale in sales:
        writer.writerow([
            sale.date.isoformat() if sale.date else '',
            sale.item.name if sale.item else 'N/A',
            sale.quantity,
            sale.unit_price,
            sale.total_price,
            sale.customer_name or 'Walk-in',
            sale.sold_by_user.name if sale.sold_by_user else 'N/A'
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=sales_report_{start_date}_to_{end_date}.csv'
    
    return response
