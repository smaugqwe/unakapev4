"""
Forecasting Routes - SARIMA Implementation
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Item, ForecastData, Sale
from datetime import datetime, date, timedelta
from sqlalchemy import func
import numpy as np

forecast_bp = Blueprint('forecast', __name__)

# Try to import statsmodels for SARIMA
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("Warning: statsmodels not available. Forecasting will use simple models.")

def generate_historical_data(item_id, months=12):
    """Generate historical sales data for an item"""
    # Get sales data aggregated by month
    today = date.today()
    start_date = today - timedelta(days=months*30)
    
    results = db.session.query(
        func.strftime('%Y-%m', Sale.date).label('month'),
        func.sum(Sale.quantity).label('quantity')
    ).filter(
        Sale.item_id == item_id,
        Sale.date >= start_date
    ).group_by(
        func.strftime('%Y-%m', Sale.date)
    ).order_by(
        func.strftime('%Y-%m', Sale.date)
    ).all()
    
    # Convert to dictionary
    data = {row.month: row.quantity for row in results}
    
    # Fill missing months with 0
    all_months = []
    current = datetime(start_date.year, start_date.month, 1)
    end = datetime(today.year, today.month, 1)
    
    while current <= end:
        month_key = current.strftime('%Y-%m')
        all_months.append({
            'month': month_key,
            'quantity': data.get(month_key, 0)
        })
        current = (current + timedelta(days=32)).replace(day=1)
    
    return all_months

def simple_forecast(historical_data, forecast_periods=3):
    """Simple forecast using moving average if statsmodels not available"""
    if len(historical_data) < 3:
        # Not enough data, return simple average
        avg = sum(historical_data) / len(historical_data) if historical_data else 0
        return [avg] * forecast_periods
    
    # Use weighted moving average (more weight to recent data)
    weights = [0.1, 0.2, 0.3, 0.4]  # Oldest to newest
    n = min(len(historical_data), len(weights))
    
    weighted_sum = sum(h[-n:] * w for h, w in zip(historical_data[-n:], weights[:n]))
    weight_sum = sum(weights[:n])
    forecast_value = weighted_sum / weight_sum
    
    # Add some variance based on recent trend
    if len(historical_data) >= 2:
        trend = (historical_data[-1] - historical_data[-2]) * 0.5
    else:
        trend = 0
    
    forecasts = []
    for i in range(forecast_periods):
        # Add decreasing trend influence
        forecasts.append(forecast_value + trend * (1 - i * 0.3))
    
    return [max(0, f) for f in forecasts]

def sarima_forecast(historical_data, forecast_periods=3):
    """SARIMA forecast using statsmodels"""
    if not STATSMODELS_AVAILABLE:
        return simple_forecast(historical_data, forecast_periods)
    
    if len(historical_data) < 6:
        return simple_forecast(historical_data, forecast_periods)
    
    try:
        # Prepare data
        data = np.array(historical_data)
        
        # SARIMA parameters: (p,d,q)(P,D,Q,s)
        # p: AR order, d: differencing, q: MA order
        # P: seasonal AR, D: seasonal differencing, Q: seasonal MA, s: seasonality (12 for monthly)
        
        # Use automatic parameter selection based on data length
        if len(data) >= 12:
            # More data, can use seasonal model
            model = SARIMAX(data, 
                          order=(1, 1, 1), 
                          seasonal_order=(1, 1, 1, 12),
                          enforce_stationarity=False,
                          enforce_invertibility=False)
        else:
            # Less data, use non-seasonal ARIMA
            model = SARIMAX(data, 
                          order=(1, 1, 1),
                          enforce_stationarity=False,
                          enforce_invertibility=False)
        
        # Fit model
        results = model.fit(disp=False)
        
        # Forecast
        forecast = results.forecast(steps=forecast_periods)
        
        # Return as list
        return [max(0, float(f)) for f in forecast]
    
    except Exception as e:
        print(f"SARIMA error: {e}")
        return simple_forecast(historical_data, forecast_periods)

def get_seasonal_pattern(historical_data):
    """Detect simple seasonal pattern"""
    if len(historical_data) < 12:
        return None
    
    # Calculate average for each month position
    monthly_avg = {}
    for i, val in enumerate(historical_data):
        month = i % 12
        if month not in monthly_avg:
            monthly_avg[month] = []
        monthly_avg[month].append(val)
    
    # Calculate average for each month
    seasonal_factors = {}
    overall_avg = sum(historical_data) / len(historical_data)
    if overall_avg > 0:
        for month, values in monthly_avg.items():
            seasonal_factors[month] = (sum(values) / len(values)) / overall_avg
    
    return seasonal_factors

@forecast_bp.route('/items', methods=['GET'])
@jwt_required()
def get_forecast_items():
    """Get items that have sales data for forecasting"""
    # Get items with sales
    items = db.session.query(
        Item.id,
        Item.name,
        Item.sku,
        func.count(Sale.id).label('sale_count'),
        func.sum(Sale.quantity).label('total_sold')
    ).join(Sale, Sale.item_id == Item.id
    ).group_by(Item.id).all()
    
    result = []
    for item in items:
        result.append({
            'id': item.id,
            'name': item.name,
            'sku': item.sku,
            'sale_count': item.sale_count,
            'total_sold': float(item.total_sold or 0)
        })
    
    return jsonify({'items': result}), 200

@forecast_bp.route('/history/<int:item_id>', methods=['GET'])
@jwt_required()
def get_forecast_history(item_id):
    """Get historical sales data for an item"""
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    months = request.args.get('months', 12, type=int)
    
    # Get historical data
    history = generate_historical_data(item_id, months)
    
    return jsonify({
        'item': item.to_dict(),
        'history': history
    }), 200

@forecast_bp.route('/predict/<int:item_id>', methods=['POST'])
@jwt_required()
def generate_forecast(item_id):
    """Generate SARIMA forecast for an item"""
    identity = get_jwt_identity()
    
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Get forecast parameters
    data = request.get_json() or {}
    forecast_periods = data.get('months', 3)
    
    # Get historical data
    history = generate_historical_data(item_id, months=24)
    
    if len(history) < 3:
        return jsonify({
            'error': 'Not enough historical data for forecasting. Need at least 3 months of sales data.',
            'history_length': len(history)
        }), 400
    
    # Extract quantities
    quantities = [h['quantity'] for h in history]
    
    # Generate forecast using SARIMA
    if STATSMODELS_AVAILABLE:
        forecasts = sarima_forecast(quantities, forecast_periods)
    else:
        forecasts = simple_forecast(quantities, forecast_periods)
    
    # Save forecast data to database
    forecast_results = []
    today = date.today()
    
    for i, pred in enumerate(forecasts):
        # Calculate the month
        forecast_month = (today.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        month_key = forecast_month.strftime('%Y-%m')
        
        # Check if forecast data exists
        existing = ForecastData.query.filter_by(
            item_id=item_id,
            month=month_key
        ).first()
        
        if existing:
            existing.predicted_quantity = pred
        else:
            forecast_data = ForecastData(
                item_id=item_id,
                month=month_key,
                predicted_quantity=pred
            )
            db.session.add(forecast_data)
        
        forecast_results.append({
            'month': month_key,
            'predicted_quantity': round(pred, 2)
        })
    
    db.session.commit()
    
    # Get stored forecast data
    stored_forecasts = ForecastData.query.filter(
        ForecastData.item_id == item_id,
        ForecastData.month >= today.strftime('%Y-%m')
    ).order_by(ForecastData.month).all()
    
    return jsonify({
        'message': 'Forecast generated successfully',
        'item': item.to_dict(),
        'history': history,
        'forecast': forecast_results,
        'model_used': 'SARIMA' if STATSMODELS_AVAILABLE else 'Simple Moving Average'
    }), 200

@forecast_bp.route('/data/<int:item_id>', methods=['GET'])
@jwt_required()
def get_forecast_data(item_id):
    """Get stored forecast data for an item"""
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Get historical data with actual and predicted
    history = generate_historical_data(item_id, months=24)
    
    # Get forecast data
    forecasts = ForecastData.query.filter_by(
        item_id=item_id
    ).order_by(ForecastData.month).all()
    
    # Combine history with forecast
    history_dict = {h['month']: h['quantity'] for h in history}
    
    combined = []
    
    # Add historical data
    for h in history:
        combined.append({
            'month': h['month'],
            'actual': h['quantity'],
            'predicted': None,
            'type': 'historical'
        })
    
    # Add forecast data
    for f in forecasts:
        month_key = f.month
        if month_key not in history_dict:  # Only future months
            combined.append({
                'month': month_key,
                'actual': None,
                'predicted': f.predicted_quantity,
                'type': 'forecast'
            })
    
    # Sort by month
    combined.sort(key=lambda x: x['month'])
    
    return jsonify({
        'item': item.to_dict(),
        'data': combined
    }), 200

@forecast_bp.route('/refresh/<int:item_id>', methods=['POST'])
@jwt_required()
def refresh_forecast(item_id):
    """Refresh/retrain forecast model"""
    return generate_forecast(item_id)
