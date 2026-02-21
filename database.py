"""
Database Setup and Seed Data
"""

from app import app, db
from models import User, Category, Supplier, Item, Batch, Lot, Sale, Transaction, ForecastData, ActivityLog
from datetime import datetime, date, timedelta
import bcrypt

def init_database():
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def seed_data():
    """Seed initial data into database"""
    with app.app_context():
        # Check if data already exists
        if User.query.first():
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding database with initial data...")
        
        # Create admin user
        admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(
            name='Admin User',
            email='admin@unakape.com',
            password=admin_password,
            role='admin',
            status='active'
        )
        db.session.add(admin)
        
        # Create owner user
        owner_password = bcrypt.hashpw('owner123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        owner = User(
            name='Owner User',
            email='owner@unakape.com',
            password=owner_password,
            role='owner',
            status='active'
        )
        db.session.add(owner)
        
        # Create employee user
        employee_password = bcrypt.hashpw('employee123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        employee = User(
            name='Employee User',
            email='employee@unakape.com',
            password=employee_password,
            role='employee',
            status='active'
        )
        db.session.add(employee)
        
        db.session.commit()
        
        # Create categories
        categories = [
            Category(name='Coffee Beans', description='Various coffee beans'),
            Category(name='Beverages', description='Ready to drink beverages'),
            Category(name='Pastries', description='Fresh pastries and baked goods'),
            Category(name='Dairy', description='Milk and dairy products'),
            Category(name='Supplies', description='Coffee shop supplies'),
            Category(name='Snacks', description='Quick snacks and treats')
        ]
        for cat in categories:
            db.session.add(cat)
        
        db.session.commit()
        
        # Create suppliers
        suppliers = [
            Supplier(name='Coffee Roasters Inc', contact='John Smith', email='john@coffeeroasters.com', phone='555-0101'),
            Supplier(name='Fresh Dairy Co', contact='Jane Doe', email='jane@freshdairy.com', phone='555-0102'),
            Supplier(name='Bakery Supply Ltd', contact='Bob Wilson', email='bob@bakerysupply.com', phone='555-0103'),
            Supplier(name='General Supplies Inc', contact='Alice Brown', email='alice@generalsupplies.com', phone='555-0104')
        ]
        for sup in suppliers:
            db.session.add(sup)
        
        db.session.commit()
        
        # Create items
        items = [
            Item(name='Espresso Beans', category_id=1, sku='COF-001', quantity=50, unit='kg', reorder_level=20, supplier_id=1, is_perishable=False),
            Item(name='House Blend', category_id=1, sku='COF-002', quantity=30, unit='kg', reorder_level=15, supplier_id=1, is_perishable=False),
            Item(name='Decaf Beans', category_id=1, sku='COF-003', quantity=15, unit='kg', reorder_level=10, supplier_id=1, is_perishable=False),
            Item(name='Colombian Beans', category_id=1, sku='COF-004', quantity=25, unit='kg', reorder_level=10, supplier_id=1, is_perishable=False),
            Item(name='Fresh Orange Juice', category_id=2, sku='BEV-001', quantity=20, unit='liters', reorder_level=10, supplier_id=2, is_perishable=True),
            Item(name='Iced Tea', category_id=2, sku='BEV-002', quantity=30, unit='liters', reorder_level=15, supplier_id=2, is_perishable=True),
            Item(name='Hot Chocolate', category_id=2, sku='BEV-003', quantity=15, unit='liters', reorder_level=8, supplier_id=2, is_perishable=True),
            Item(name='Smoothie Mix', category_id=2, sku='BEV-004', quantity=10, unit='liters', reorder_level=5, supplier_id=2, is_perishable=True),
            Item(name='Croissants', category_id=3, sku='PAS-001', quantity=50, unit='pcs', reorder_level=20, supplier_id=3, is_perishable=True),
            Item(name='Muffins', category_id=3, sku='PAS-002', quantity=40, unit='pcs', reorder_level=15, supplier_id=3, is_perishable=True),
            Item(name='Danishes', category_id=3, sku='PAS-003', quantity=30, unit='pcs', reorder_level=10, supplier_id=3, is_perishable=True),
            Item(name='Scones', category_id=3, sku='PAS-004', quantity=25, unit='pcs', reorder_level=10, supplier_id=3, is_perishable=True),
            Item(name='Whole Milk', category_id=4, sku='DAI-001', quantity=20, unit='liters', reorder_level=10, supplier_id=2, is_perishable=True),
            Item(name='Skim Milk', category_id=4, sku='DAI-002', quantity=15, unit='liters', reorder_level=8, supplier_id=2, is_perishable=True),
            Item(name='Cream', category_id=4, sku='DAI-003', quantity=10, unit='liters', reorder_level=5, supplier_id=2, is_perishable=True),
            Item(name='Coffee Cups', category_id=5, sku='SUP-001', unit='pcs', quantity=500, reorder_level=200, supplier_id=4, is_perishable=False),
            Item(name='Sugar Sticks', category_id=5, sku='SUP-002', quantity=1000, unit='pcs', reorder_level=300, supplier_id=4, is_perishable=False),
            Item(name='Stirrers', category_id=5, sku='SUP-003', quantity=800, unit='pcs', reorder_level=200, supplier_id=4, is_perishable=False),
            Item(name='Cookies', category_id=6, sku='SNK-001', quantity=60, unit='pcs', reorder_level=25, supplier_id=4, is_perishable=True),
            Item(name='Brownies', category_id=6, sku='SNK-002', quantity=40, unit='pcs', reorder_level=15, supplier_id=4, is_perishable=True)
        ]
        
        for item in items:
            db.session.add(item)
        
        db.session.commit()
        
        # Create batches for non-perishable items
        batches = [
            Batch(item_id=1, batch_number='BATCH-20240101-001', production_date=date.today() - timedelta(days=30), quantity=50, remaining_quantity=50, status='active'),
            Batch(item_id=2, batch_number='BATCH-20240101-002', production_date=date.today() - timedelta(days=25), quantity=30, remaining_quantity=30, status='active'),
            Batch(item_id=3, batch_number='BATCH-20240101-003', production_date=date.today() - timedelta(days=20), quantity=15, remaining_quantity=15, status='active'),
            Batch(item_id=4, batch_number='BATCH-20240101-004', production_date=date.today() - timedelta(days=15), quantity=25, remaining_quantity=25, status='active'),
        ]
        
        for batch in batches:
            db.session.add(batch)
        
        db.session.commit()
        
        # Create lots for perishable items
        lots = [
            Lot(item_id=5, lot_number='LOT-20240105-001', expiration_date=date.today() + timedelta(days=5), quantity=10, remaining_quantity=10, status='active'),
            Lot(item_id=5, lot_number='LOT-20240108-001', expiration_date=date.today() + timedelta(days=8), quantity=10, remaining_quantity=10, status='active'),
            Lot(item_id=6, lot_number='LOT-20240110-001', expiration_date=date.today() + timedelta(days=30), quantity=30, remaining_quantity=30, status='active'),
            Lot(item_id=7, lot_number='LOT-20240103-001', expiration_date=date.today() + timedelta(days=3), quantity=15, remaining_quantity=15, status='active'),
            Lot(item_id=9, lot_number='LOT-20240112-001', expiration_date=date.today(), quantity=25, remaining_quantity=25, status='active'),
            Lot(item_id=9, lot_number='LOT-20240110-001', expiration_date=date.today() + timedelta(days=2), quantity=25, remaining_quantity=25, status='active'),
            Lot(item_id=10, lot_number='LOT-20240111-001', expiration_date=date.today() + timedelta(days=7), quantity=40, remaining_quantity=40, status='active'),
            Lot(item_id=13, lot_number='LOT-20240101-001', expiration_date=date.today() - timedelta(days=2), quantity=10, remaining_quantity=10, status='expired'),
            Lot(item_id=15, lot_number='LOT-20240108-001', expiration_date=date.today() + timedelta(days=4), quantity=10, remaining_quantity=10, status='active')
        ]
        
        for lot in lots:
            db.session.add(lot)
        
        db.session.commit()
        
        # Create some sample sales for forecasting data
        today = date.today()
        item_id = 1  # Espresso Beans
        
        import random
        for i in range(12):
            month_date = today - timedelta(days=(11-i)*30)
            qty = random.randint(20, 40)
            
            sale = Sale(
                item_id=item_id,
                quantity=qty,
                unit_price=25.0,
                total_price=qty * 25.0,
                sold_by=1,
                date=month_date
            )
            db.session.add(sale)
        
        db.session.commit()
        
        # Create some transactions
        transactions = [
            Transaction(user_id=1, action='ADD', item_id=1, quantity=50, details='Initial stock for Espresso Beans'),
            Transaction(user_id=1, action='ADD', item_id=5, quantity=20, details='Initial stock for Fresh Orange Juice'),
            Transaction(user_id=1, action='ADD', item_id=9, quantity=50, details='Initial stock for Croissants'),
            Transaction(user_id=1, action='ADD', item_id=13, quantity=20, details='Initial stock for Whole Milk'),
            Transaction(user_id=2, action='SALE', item_id=1, quantity=-5, details='Sale of Espresso Beans'),
            Transaction(user_id=2, action='SALE', item_id=5, quantity=-3, details='Sale of Fresh Orange Juice'),
            Transaction(user_id=3, action='SALE', item_id=9, quantity=-10, details='Sale of Croissants'),
        ]
        
        for trans in transactions:
            db.session.add(trans)
        
        db.session.commit()
        
        # Create activity log
        logs = [
            ActivityLog(user_id=1, action='System initialized', details='Database initialized with seed data'),
            ActivityLog(user_id=1, action='User registered', details='Admin user created'),
            ActivityLog(user_id=1, action='User created', details='Employee user created'),
        ]
        
        for log in logs:
            db.session.add(log)
        
        db.session.commit()
        
        print("Database seeded successfully!")
        print("\n=== Default Login Credentials ===")
        print("Admin: admin@unakape.com / admin123")
        print("Owner: owner@unakape.com / owner123")
        print("Employee: employee@unakape.com / employee123")

if __name__ == '__main__':
    init_database()
    seed_data()
