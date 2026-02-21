"""
Unakape - Database Models
"""

from app import db
from datetime import datetime

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin, employee, owner
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    sales = db.relationship('Sale', backref='sold_by_user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    """Category model"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Supplier(db.Model):
    """Supplier model"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', backref='supplier', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Item(db.Model):
    """Item model for inventory"""
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    sku = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='pcs')  # pcs, kg, liters, etc.
    reorder_level = db.Column(db.Integer, default=10)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    description = db.Column(db.Text)
    is_perishable = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    batches = db.relationship('Batch', backref='item', lazy=True)
    lots = db.relationship('Lot', backref='item', lazy=True)
    sales = db.relationship('Sale', backref='item', lazy=True)
    transactions = db.relationship('Transaction', backref='item', lazy=True)
    forecast_data = db.relationship('ForecastData', backref='item', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'sku': self.sku,
            'quantity': self.quantity,
            'unit': self.unit,
            'reorder_level': self.reorder_level,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'description': self.description,
            'is_perishable': self.is_perishable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Batch(db.Model):
    """Batch model for produced items"""
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    batch_number = db.Column(db.String(50), unique=True, nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    remaining_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, consumed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='batch', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'batch_number': self.batch_number,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'quantity': self.quantity,
            'remaining_quantity': self.remaining_quantity,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Lot(db.Model):
    """Lot model for perishables"""
    __tablename__ = 'lots'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    lot_number = db.Column(db.String(50), unique=True, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    remaining_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, expiring_soon, expired, consumed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='lot', lazy=True)
    
    def get_expiry_status(self):
        """Get expiry status: safe, expiring_soon, expired"""
        if not self.expiration_date:
            return 'safe'
        today = datetime.now().date()
        days_until_expiry = (self.expiration_date - today).days
        
        if days_until_expiry < 0:
            return 'expired'
        elif days_until_expiry <= 7:
            return 'expiring_soon'
        return 'safe'
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'lot_number': self.lot_number,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'quantity': self.quantity,
            'remaining_quantity': self.remaining_quantity,
            'status': self.status,
            'expiry_status': self.get_expiry_status(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Sale(db.Model):
    """Sale model"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    lot_id = db.Column(db.Integer, db.ForeignKey('lots.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)
    sold_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    customer_name = db.Column(db.String(100))
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'batch_id': self.batch_id,
            'batch_number': self.batch.batch_number if self.batch else None,
            'lot_id': self.lot_id,
            'lot_number': self.lot.lot_number if self.lot else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'sold_by': self.sold_by,
            'sold_by_name': self.sold_by_user.name if self.sold_by_user else None,
            'customer_name': self.customer_name,
            'notes': self.notes,
            'date': self.date.isoformat() if self.date else None
        }

class Transaction(db.Model):
    """Transaction log model"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # ADD, SALE, UPDATE, DELETE
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    reference_id = db.Column(db.Integer)  # batch_id or lot_id or sale_id
    reference_type = db.Column(db.String(20))  # batch, lot, sale
    quantity = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type,
            'quantity': self.quantity,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ForecastData(db.Model):
    """Forecast data model"""
    __tablename__ = 'forecast_data'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    actual_quantity = db.Column(db.Integer, default=0)
    predicted_quantity = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('item_id', 'month', name='unique_item_month'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'month': self.month,
            'actual_quantity': self.actual_quantity,
            'predicted_quantity': self.predicted_quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ActivityLog(db.Model):
    """Activity log for admin"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
