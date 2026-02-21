"""
Unakape - Daily Inventory Monitoring System
Main Flask Application
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import bcrypt

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'unakape_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/unakape'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'unakape_jwt_secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
CORS(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Import routes
from routes.auth import auth_bp
from routes.items import items_bp
from routes.batches import batches_bp
from routes.lots import lots_bp
from routes.sales import sales_bp
from routes.dashboard import dashboard_bp
from routes.forecasting import forecast_bp
from routes.reports import reports_bp
from routes.admin import admin_bp
from routes.transactions import transactions_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(items_bp, url_prefix='/api/items')
app.register_blueprint(batches_bp, url_prefix='/api/batches')
app.register_blueprint(lots_bp, url_prefix='/api/lots')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(forecast_bp, url_prefix='/api/forecast')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(transactions_bp, url_prefix='/api/transactions')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'app': 'Unakape Inventory System'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
