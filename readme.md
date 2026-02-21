# Unakape - Daily Inventory Monitoring System

A comprehensive inventory monitoring system with real-time dashboard, batch/lot tracking, SARIMA-based demand forecasting, and role-based access control.

## Features

### Authentication & Authorization
- User registration and login with JWT tokens
- Role-based access control (Admin, Employee, Owner)
- Password hashing with bcrypt
- Session management

### Inventory Management
- Full CRUD operations for items
- Category and supplier management
- SKU-based item tracking
- Reorder level alerts
- Batch tracking for produced items
- Lot tracking for perishables with expiry management

### Dashboard
- Real-time KPIs: Total Items, Categories, Low Stock, Expiring Soon
- Action Center with alerts
- Stock Levels per Category (Bar Chart)
- Expiration Risk Overview (Doughnut Chart)
- Recent Transactions

### Forecasting (SARIMA)
- Monthly demand forecasting using SARIMA model
- 3-month predictions
- Actual vs Forecast comparison chart
- Historical data analysis

### Sales & Transactions
- Sales module with automatic stock deduction
- Batch/Lot specific deduction
- Prevention of expired lot sales
- Complete transaction logging

### Reports
- Daily Inventory Report
- Sales Report
- Expiry Report
- Forecast Report
- Export to CSV

### Admin Panel
- User management (Add, Edit, Deactivate)
- Activity logs
- System statistics

## Tech Stack

### Backend
- **Python Flask** - Web framework
- **SQLAlchemy** - ORM
- **PyMySQL** - MySQL connector
- **Flask-JWT-Extended** - JWT authentication
- **statsmodels** - SARIMA forecasting

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling (Dark café theme)
- **Vanilla JavaScript** - Frontend logic
- **Chart.js** - Data visualization
- **Font Awesome** - Icons

### Database
- **MySQL** - Relational database

## Project Structure

```
unakapev3/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── database.py            # Database setup and seed data
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── index.html             # Frontend HTML
├── design.css             # Frontend styles
├── test.js                # Frontend JavaScript
├── routes/
│   ├── __init__.py
│   ├── auth.py            # Authentication routes
│   ├── items.py           # Item management routes
│   ├── batches.py         # Batch tracking routes
│   ├── lots.py            # Lot/perishable routes
│   ├── sales.py           # Sales routes
│   ├── dashboard.py       # Dashboard KPIs
│   ├── forecasting.py     # SARIMA forecasting
│   ├── reports.py        # Report generation
│   ├── admin.py          # Admin panel routes
│   └── transactions.py   # Transaction logs
└── docs/                  # Documentation
```

## Installation

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Node.js (optional, for development)

### 1. Setup MySQL Database

```
sql
CREATE DATABASE unakape CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Update the database connection string in `app.py`:
```
python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/unakape'
```

### 2. Install Python Dependencies

```
bash
pip install -r requirements.txt
```

### 3. Initialize Database

```
bash
python database.py
```

This will create all tables and seed initial data.

### 4. Run the Server

```
bash
python app.py
```

The server will start on `http://localhost:5000`

### 5. Access the Application

Open `http://localhost:5000` in your browser.

## Default Login Credentials

| Role   | Email                  | Password     |
|--------|------------------------|--------------|
| Admin  | admin@unakape.com      | admin123     |
| Owner  | owner@unakape.com      | owner123     |
| Employee | employee@unakape.com | employee123  |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user

### Items
- `GET /api/items` - Get all items
- `POST /api/items` - Create item
- `GET /api/items/:id` - Get item
- `PUT /api/items/:id` - Update item
- `DELETE /api/items/:id` - Delete item

### Categories
- `GET /api/items/categories` - Get categories
- `POST /api/items/categories` - Create category

### Batches
- `GET /api/batches` - Get batches
- `POST /api/batches` - Create batch
- `DELETE /api/batches/:id` - Delete batch

### Lots
- `GET /api/lots` - Get lots
- `POST /api/lots` - Create lot
- `GET /api/lots/expiring` - Get expiring lots
- `DELETE /api/lots/:id` - Delete lot

### Sales
- `GET /api/sales` - Get sales
- `POST /api/sales` - Create sale
- `DELETE /api/sales/:id` - Cancel sale

### Dashboard
- `GET /api/dashboard/kpis` - Get KPIs
- `GET /api/dashboard/alerts` - Get alerts
- `GET /api/dashboard/stock-by-category` - Get stock chart data
- `GET /api/dashboard/expiry-overview` - Get expiry data

### Forecasting
- `GET /api/forecast/items` - Get forecastable items
- `POST /api/forecast/predict/:id` - Generate forecast
- `GET /api/forecast/data/:id` - Get forecast data

### Reports
- `GET /api/reports/inventory` - Inventory report
- `GET /api/reports/sales` - Sales report
- `GET /api/reports/expiry` - Expiry report
- `GET /api/reports/forecast` - Forecast report
- `GET /api/reports/export/inventory/csv` - Export CSV

### Admin
- `GET /api/admin/users` - Get users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/:id` - Update user
- `DELETE /api/admin/users/:id` - Deactivate user
- `GET /api/admin/activity-logs` - Get activity logs
- `GET /api/admin/stats` - Get system stats

### Transactions
- `GET /api/transactions` - Get transactions
- `GET /api/transactions/actions` - Get action types

## Database Schema

### users
| Column     | Type         | Description           |
|------------|--------------|----------------------|
| id         | INT          | Primary key          |
| name       | VARCHAR(100) | User's full name    |
| email      | VARCHAR(120) | Unique email         |
| password   | VARCHAR(255) | Hashed password     |
| role       | VARCHAR(20)  | admin/employee/owner|
| status     | VARCHAR(20)  | active/inactive     |
| created_at | DATETIME     | Creation timestamp  |

### categories
| Column      | Type         | Description     |
|-------------|--------------|-----------------|
| id          | INT          | Primary key     |
| name        | VARCHAR(100) | Category name  |
| description | VARCHAR(255) | Description    |

### suppliers
| Column    | Type         | Description      |
|-----------|--------------|------------------|
| id        | INT          | Primary key      |
| name      | VARCHAR(100) | Supplier name   |
| contact   | VARCHAR(100) | Contact person  |
| email     | VARCHAR(120) | Email address   |
| phone     | VARCHAR(20)  | Phone number    |
| address   | TEXT         | Full address    |

### items
| Column         | Type         | Description              |
|----------------|--------------|--------------------------|
| id             | INT          | Primary key              |
| name           | VARCHAR(100) | Item name               |
| category_id    | INT          | Foreign key to category |
| sku            | VARCHAR(50)  | Stock keeping unit      |
| quantity       | INT          | Current quantity        |
| unit           | VARCHAR(20)  | Unit of measurement     |
| reorder_level  | INT          | Reorder threshold       |
| supplier_id    | INT          | Foreign key to supplier |
| is_perishable  | BOOLEAN      | Is item perishable?     |

### batches
| Column           | Type         | Description             |
|------------------|--------------|-------------------------|
| id               | INT          | Primary key             |
| item_id          | INT          | Foreign key to item     |
| batch_number     | VARCHAR(50)  | Unique batch number     |
| production_date  | DATE         | Production date         |
| quantity         | INT          | Original quantity       |
| remaining_quantity | INT       | Remaining quantity      |
| status           | VARCHAR(20)  | active/consumed         |

### lots
| Column           | Type         | Description             |
|------------------|--------------|-------------------------|
| id               | INT          | Primary key             |
| item_id          | INT          | Foreign key to item     |
| lot_number       | VARCHAR(50)  | Unique lot number      |
| expiration_date  | DATE         | Expiration date        |
| quantity         | INT          | Original quantity      |
| remaining_quantity | INT       | Remaining quantity     |
| status           | VARCHAR(20)  | active/expired/etc.    |

### sales
| Column       | Type         | Description        |
|--------------|--------------|--------------------|
| id           | INT          | Primary key        |
| item_id      | INT          | Foreign key to item|
| batch_id     | INT          | Foreign key to batch|
| lot_id       | INT          | Foreign key to lot |
| quantity     | INT          | Sold quantity      |
| unit_price   | FLOAT        | Price per unit     |
| total_price  | FLOAT        | Total price        |
| sold_by      | INT          | Foreign key to user|
| date         | DATETIME     | Sale date          |

### transactions
| Column        | Type         | Description        |
|---------------|--------------|--------------------|
| id            | INT          | Primary key        |
| user_id       | INT          | Foreign key to user|
| action        | VARCHAR(50)  | ADD/SALE/UPDATE/DELETE|
| item_id       | INT          | Foreign key to item|
| reference_id  | INT          | Reference ID       |
| reference_type| VARCHAR(20)  | Reference type     |
| quantity      | INT          | Quantity change   |
| details       | TEXT         | Additional details|
| created_at    | DATETIME     | Transaction time  |

### forecast_data
| Column            | Type         | Description          |
|-------------------|--------------|----------------------|
| id                | INT          | Primary key          |
| item_id           | INT          | Foreign key to item  |
| month             | VARCHAR(7)   | YYYY-MM format       |
| actual_quantity   | INT          | Actual sales quantity|
| predicted        | Predicted_quantity| FLOAT quantity  |

### activity_logs
| Column     | Type         | Description        |
|------------|--------------|--------------------|
| id         | INT          | Primary key        |
| user_id    | INT          | Foreign key to user|
| action     | VARCHAR(100) | Action description |
| details    | TEXT         | Additional details |
| created_at | DATETIME     | Log timestamp      |

## Forecasting Model

The system uses SARIMA (Seasonal AutoRegressive Integrated Moving Average) for demand forecasting:

- **Order parameters**: (p, d, q) - Non-seasonal component
- **Seasonal order**: (P, D, Q, s) - Seasonal component (s=12 for monthly)
- Uses historical sales data to predict future demand

If statsmodels is not available, falls back to a simple weighted moving average.

## UI Theme

The application uses a café-inspired dark theme with:
- Primary Brown: #6F4E37
- Accent Orange: #E67E22
- Dark backgrounds with clean card layouts
- Responsive design for all screen sizes

## License

This project is for educational purposes.
