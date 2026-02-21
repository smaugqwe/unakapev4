/**
 * Unakape - Inventory Monitoring System
 * Frontend JavaScript
 */

// API Base URL
const API_URL = 'http://localhost:5000/api';

// Global state
let currentUser = null;
let token = localStorage.getItem('token');
let charts = {};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        checkAuth();
    } else {
        showLoginPage();
    }
    
    // Setup navigation
    setupNavigation();
    
    // Setup form handlers
    setupFormHandlers();
});

// Authentication
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            showApp();
        } else {
            localStorage.removeItem('token');
            token = null;
            showLoginPage();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLoginPage();
    }
}

function showLoginPage() {
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('register-page').style.display = 'none';
    document.getElementById('app-container').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('register-page').style.display = 'flex';
}

function showApp() {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('register-page').style.display = 'none';
    document.getElementById('app-container').style.display = 'flex';
    
    // Update user info
    document.getElementById('user-name').textContent = currentUser.name;
    document.getElementById('user-role-badge').textContent = currentUser.role;
    
    // Show admin panel if admin or owner
    if (currentUser.role === 'admin' || currentUser.role === 'owner') {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'flex');
    }
    
    // Load dashboard
    navigateTo('dashboard');
}

function setupFormHandlers() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                token = data.access_token;
                currentUser = data.user;
                localStorage.setItem('token', token);
                showApp();
            } else {
                alert(data.error || 'Login failed');
            }
        } catch (error) {
            alert('Login failed. Make sure the server is running.');
        }
    });
    
    // Register form
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('register-name').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, role: 'employee' })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Registration successful! Please login.');
                showLogin();
            } else {
                alert(data.error || 'Registration failed');
            }
        } catch (error) {
            alert('Registration failed. Make sure the server is running.');
        }
    });
}

function logout() {
    localStorage.removeItem('token');
    token = null;
    currentUser = null;
    showLoginPage();
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateTo(page);
        });
    });
}

function navigateTo(page) {
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });
    
    // Show page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    
    // Load page data
    switch (page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'inventory':
            loadItems();
            loadCategories();
            break;
        case 'batches':
            loadBatches();
            break;
        case 'lots':
            loadLots();
            break;
        case 'sales':
            loadSales();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'forecasting':
            loadForecastItems();
            break;
        case 'reports':
            break;
        case 'admin':
            if (currentUser.role === 'admin' || currentUser.role === 'owner') {
                loadAdminData();
            }
            break;
    }
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }
    
    return response;
}

// Dashboard
async function loadDashboard() {
    try {
        // Load KPIs
        const kpiResponse = await apiCall('/dashboard/kpis');
        const kpiData = await kpiResponse.json();
        
        document.getElementById('kpi-total-items').textContent = kpiData.total_items;
        document.getElementById('kpi-categories').textContent = kpiData.total_categories;
        document.getElementById('kpi-low-stock').textContent = kpiData.low_stock_alerts;
        document.getElementById('kpi-expiring').textContent = kpiData.expiring_soon;
        
        // Load alerts
        const alertsResponse = await apiCall('/dashboard/alerts');
        const alertsData = await alertsResponse.json();
        
        const alertsList = document.getElementById('alerts-list');
        if (alertsData.alerts.length === 0) {
            alertsList.innerHTML = '<div class="alert-item">No alerts at this time</div>';
        } else {
            alertsList.innerHTML = alertsData.alerts.slice(0, 10).map(alert => `
                <div class="alert-item ${alert.severity}">
                    <i class="fas ${alert.severity === 'critical' ? 'fa-exclamation-circle' : 'fa-exclamation-triangle'}"></i>
                    <div>
                        <div class="alert-title">${alert.title}</div>
                        <div class="alert-message">${alert.message}</div>
                    </div>
                </div>
            `).join('');
        }
        
        // Load stock chart
        loadStockChart();
        
        // Load expiry chart
        loadExpiryChart();
        
        // Load recent transactions
        loadRecentTransactions();
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

async function loadStockChart() {
    try {
        const response = await apiCall('/dashboard/stock-by-category');
        const data = await response.json();
        
        const ctx = document.getElementById('stock-chart').getContext('2d');
        
        if (charts.stock) {
            charts.stock.destroy();
        }
        
        charts.stock = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.categories,
                datasets: [{
                    label: 'Stock Quantity',
                    data: data.quantities,
                    backgroundColor: '#E67E22',
                    borderColor: '#F39C12',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#3d3d3d' },
                        ticks: { color: '#a0a0a0' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#a0a0a0' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load stock chart:', error);
    }
}

async function loadExpiryChart() {
    try {
        const response = await apiCall('/dashboard/expiry-overview');
        const data = await response.json();
        
        const ctx = document.getElementById('expiry-chart').getContext('2d');
        
        if (charts.expiry) {
            charts.expiry.destroy();
        }
        
        charts.expiry = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Safe', 'Expiring Soon', 'Expired'],
                datasets: [{
                    data: [data.safe, data.expiring_soon, data.expired],
                    backgroundColor: ['#27ae60', '#f39c12', '#e74c3c'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#a0a0a0' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load expiry chart:', error);
    }
}

async function loadRecentTransactions() {
    try {
        const response = await apiCall('/dashboard/recent-transactions?limit=5');
        const data = await response.json();
        
        const tbody = document.getElementById('recent-transactions');
        tbody.innerHTML = data.transactions.map(t => `
            <tr>
                <td>${new Date(t.created_at).toLocaleDateString()}</td>
                <td><span class="status-badge ${t.action.toLowerCase()}">${t.action}</span></td>
                <td>${t.item_name || '-'}</td>
                <td>${t.quantity || 0}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

// Items
async function loadItems() {
    try {
        const response = await apiCall('/items');
        const data = await response.json();
        
        const tbody = document.getElementById('items-table');
        tbody.innerHTML = data.items.map(item => `
            <tr>
                <td>${item.sku}</td>
                <td>${item.name}</td>
                <td>${item.category_name || '-'}</td>
                <td>${item.quantity}</td>
                <td>${item.unit}</td>
                <td>${item.reorder_level}</td>
                <td>
                    <span class="status-badge ${item.quantity <= item.reorder_level ? 'low-stock' : 'active'}">
                        ${item.quantity <= item.reorder_level ? 'Low Stock' : 'OK'}
                    </span>
                </td>
                <td>
                    <button class="action-btn" onclick="editItem(${item.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn danger" onclick="deleteItem(${item.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load items:', error);
    }
}

async function loadCategories() {
    try {
        const response = await apiCall('/items/categories');
        const data = await response.json();
        
        const filterSelect = document.getElementById('filter-category');
        filterSelect.innerHTML = '<option value="">All Categories</option>' + 
            data.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        
        // Also update modal selects
        if (document.getElementById('modal-content').innerHTML) {
            const categorySelect = document.getElementById('item-category');
            if (categorySelect) {
                categorySelect.innerHTML = data.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            }
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

function showAddItemModal() {
    loadCategories().then(() => {
        const content = `
            <form class="modal-form" onsubmit="saveItem(event)">
                <div class="form-group">
                    <label>Item Name *</label>
                    <input type="text" id="item-name" required>
                </div>
                <div class="form-group">
                    <label>Category *</label>
                    <select id="item-category" required></select>
                </div>
                <div class="form-group">
                    <label>SKU *</label>
                    <input type="text" id="item-sku" required>
                </div>
                <div class="form-group">
                    <label>Quantity</label>
                    <input type="number" id="item-quantity" value="0" min="0">
                </div>
                <div class="form-group">
                    <label>Unit</label>
                    <select id="item-unit">
                        <option value="pcs">Pieces</option>
                        <option value="kg">Kilograms</option>
                        <option value="liters">Liters</option>
                        <option value="boxes">Boxes</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Reorder Level</label>
                    <input type="number" id="item-reorder" value="10" min="0">
                </div>
                <div class="form-group">
                    <label>Is Perishable</label>
                    <input type="checkbox" id="item-perishable">
                </div>
                <div class="modal-form-actions">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn-primary">Save Item</button>
                </div>
            </form>
        `;
        
        showModal('Add New Item', content);
        
        // Populate category select
        const select = document.getElementById('item-category');
        const categories = document.getElementById('filter-category').options;
        for (let i = 1; i < categories.length; i++) {
            select.innerHTML += `<option value="${categories[i].value}">${categories[i].text}</option>`;
        }
    });
}

async function saveItem(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('item-name').value,
        category_id: parseInt(document.getElementById('item-category').value),
        sku: document.getElementById('item-sku').value,
        quantity: parseInt(document.getElementById('item-quantity').value),
        unit: document.getElementById('item-unit').value,
        reorder_level: parseInt(document.getElementById('item-reorder').value),
        is_perishable: document.getElementById('item-perishable').checked
    };
    
    try {
        const response = await apiCall('/items', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadItems();
            alert('Item added successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to add item');
        }
    } catch (error) {
        alert('Failed to add item');
    }
}

async function deleteItem(id) {
    if (!confirm('Are you sure you want to delete this item?')) return;
    
    try {
        const response = await apiCall(`/items/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            loadItems();
            alert('Item deleted successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to delete item');
        }
    } catch (error) {
        alert('Failed to delete item');
    }
}

// Batches
async function loadBatches() {
    try {
        const response = await apiCall('/batches');
        const data = await response.json();
        
        const tbody = document.getElementById('batches-table');
        tbody.innerHTML = data.batches.map(batch => `
            <tr>
                <td>${batch.batch_number}</td>
                <td>${batch.item_name}</td>
                <td>${batch.production_date}</td>
                <td>${batch.quantity}</td>
                <td>${batch.remaining_quantity}</td>
                <td><span class="status-badge ${batch.status}">${batch.status}</span></td>
                <td>
                    <button class="action-btn danger" onclick="deleteBatch(${batch.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load batches:', error);
    }
}

function showAddBatchModal() {
    loadItems().then(() => {
        const content = `
            <form class="modal-form" onsubmit="saveBatch(event)">
                <div class="form-group">
                    <label>Item *</label>
                    <select id="batch-item" required></select>
                </div>
                <div class="form-group">
                    <label>Production Date *</label>
                    <input type="date" id="batch-production-date" required>
                </div>
                <div class="form-group">
                    <label>Quantity *</label>
                    <input type="number" id="batch-quantity" required min="1">
                </div>
                <div class="modal-form-actions">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn-primary">Save Batch</button>
                </div>
            </form>
        `;
        
        showModal('Add New Batch', content);
        
        // Populate item select
        const select = document.getElementById('batch-item');
        const items = document.getElementById('items-table').querySelectorAll('tr');
        // This is a simplified version - in production, you'd fetch items properly
    });
}

async function saveBatch(e) {
    e.preventDefault();
    
    const data = {
        item_id: parseInt(document.getElementById('batch-item').value),
        production_date: document.getElementById('batch-production-date').value,
        quantity: parseInt(document.getElementById('batch-quantity').value)
    };
    
    try {
        const response = await apiCall('/batches', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadBatches();
            alert('Batch added successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to add batch');
        }
    } catch (error) {
        alert('Failed to add batch');
    }
}

async function deleteBatch(id) {
    if (!confirm('Are you sure you want to delete this batch?')) return;
    
    try {
        const response = await apiCall(`/batches/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            loadBatches();
            alert('Batch deleted successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to delete batch');
        }
    } catch (error) {
        alert('Failed to delete batch');
    }
}

// Lots
async function loadLots() {
    try {
        const response = await apiCall('/lots');
        const data = await response.json();
        
        const tbody = document.getElementById('lots-table');
        tbody.innerHTML = data.lots.map(lot => {
            const status = lot.expiry_status || lot.status;
            return `
                <tr>
                    <td>${lot.lot_number}</td>
                    <td>${lot.item_name}</td>
                    <td>${lot.expiration_date}</td>
                    <td>${lot.quantity}</td>
                    <td>${lot.remaining_quantity}</td>
                    <td><span class="status-badge ${status}">${status.replace('_', ' ')}</span></td>
                    <td>
                        <button class="action-btn danger" onclick="deleteLot(${lot.id})"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load lots:', error);
    }
}

function showAddLotModal() {
    const content = `
        <form class="modal-form" onsubmit="saveLot(event)">
            <div class="form-group">
                <label>Item *</label>
                <select id="lot-item" required></select>
            </div>
            <div class="form-group">
                <label>Expiration Date *</label>
                <input type="date" id="lot-expiration-date" required>
            </div>
            <div class="form-group">
                <label>Quantity *</label>
                <input type="number" id="lot-quantity" required min="1">
            </div>
            <div class="modal-form-actions">
                <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn-primary">Save Lot</button>
            </div>
        </form>
    `;
    
    showModal('Add New Lot', content);
}

async function saveLot(e) {
    e.preventDefault();
    
    const data = {
        item_id: parseInt(document.getElementById('lot-item').value),
        expiration_date: document.getElementById('lot-expiration-date').value,
        quantity: parseInt(document.getElementById('lot-quantity').value)
    };
    
    try {
        const response = await apiCall('/lots', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadLots();
            alert('Lot added successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to add lot');
        }
    } catch (error) {
        alert('Failed to add lot');
    }
}

async function deleteLot(id) {
    if (!confirm('Are you sure you want to delete this lot?')) return;
    
    try {
        const response = await apiCall(`/lots/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            loadLots();
            alert('Lot deleted successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to delete lot');
        }
    } catch (error) {
        alert('Failed to delete lot');
    }
}

// Sales
async function loadSales() {
    try {
        const response = await apiCall('/sales');
        const data = await response.json();
        
        const tbody = document.getElementById('sales-table');
        tbody.innerHTML = data.sales.map(sale => `
            <tr>
                <td>${new Date(sale.date).toLocaleDateString()}</td>
                <td>${sale.item_name}</td>
                <td>${sale.quantity}</td>
                <td>$${sale.unit_price.toFixed(2)}</td>
                <td>$${sale.total_price.toFixed(2)}</td>
                <td>${sale.sold_by_name}</td>
                <td>
                    <button class="action-btn danger" onclick="deleteSale(${sale.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load sales:', error);
    }
}

function showAddSaleModal() {
    const content = `
        <form class="modal-form" onsubmit="saveSale(event)">
            <div class="form-group">
                <label>Item *</label>
                <select id="sale-item" required></select>
            </div>
            <div class="form-group">
                <label>Quantity *</label>
                <input type="number" id="sale-quantity" required min="1">
            </div>
            <div class="form-group">
                <label>Unit Price</label>
                <input type="number" id="sale-price" step="0.01" value="0">
            </div>
            <div class="form-group">
                <label>Customer Name</label>
                <input type="text" id="sale-customer" placeholder="Walk-in">
            </div>
            <div class="modal-form-actions">
                <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn-primary">Complete Sale</button>
            </div>
        </form>
    `;
    
    showModal('New Sale', content);
}

async function saveSale(e) {
    e.preventDefault();
    
    const data = {
        item_id: parseInt(document.getElementById('sale-item').value),
        quantity: parseInt(document.getElementById('sale-quantity').value),
        unit_price: parseFloat(document.getElementById('sale-price').value) || 0,
        customer_name: document.getElementById('sale-customer').value || null
    };
    
    try {
        const response = await apiCall('/sales', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadSales();
            loadDashboard();
            alert('Sale completed successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to complete sale');
        }
    } catch (error) {
        alert('Failed to complete sale');
    }
}

async function deleteSale(id) {
    if (!confirm('Are you sure you want to cancel this sale?')) return;
    
    try {
        const response = await apiCall(`/sales/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            loadSales();
            loadDashboard();
            alert('Sale cancelled successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to cancel sale');
        }
    } catch (error) {
        alert('Failed to cancel sale');
    }
}

// Transactions
async function loadTransactions() {
    try {
        const response = await apiCall('/transactions?limit=50');
        const data = await response.json();
        
        const tbody = document.getElementById('transactions-table');
        tbody.innerHTML = data.transactions.map(t => `
            <tr>
                <td>${new Date(t.created_at).toLocaleString()}</td>
                <td>${t.user_name}</td>
                <td><span class="status-badge ${t.action.toLowerCase()}">${t.action}</span></td>
                <td>${t.item_name || '-'}</td>
                <td>${t.quantity || 0}</td>
                <td>${t.details || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

// Forecasting
async function loadForecastItems() {
    try {
        const response = await apiCall('/forecast/items');
        const data = await response.json();
        
        const select = document.getElementById('forecast-item');
        select.innerHTML = '<option value="">Select Item</option>' + 
            data.items.map(i => `<option value="${i.id}">${i.name} (${i.sku})</option>`).join('');
    } catch (error) {
        console.error('Failed to load forecast items:', error);
    }
}

async function generateForecast() {
    const itemId = document.getElementById('forecast-item').value;
    if (!itemId) {
        alert('Please select an item');
        return;
    }
    
    try {
        const response = await apiCall(`/forecast/predict/${itemId}`, {
            method: 'POST',
            body: JSON.stringify({ months: 3 })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update forecast results
            const resultsDiv = document.getElementById('forecast-results');
            resultsDiv.innerHTML = data.forecast.map(f => `
                <div class="forecast-month">
                    <h4>${f.month}</h4>
                    <p>${f.predicted_quantity.toFixed(2)}</p>
                </div>
            `).join('');
            
            // Update chart
            updateForecastChart(data.history, data.forecast);
        } else {
            alert(data.error || 'Failed to generate forecast');
        }
    } catch (error) {
        alert('Failed to generate forecast');
    }
}

function updateForecastChart(history, forecast) {
    const ctx = document.getElementById('forecast-chart').getContext('2d');
    
    if (charts.forecast) {
        charts.forecast.destroy();
    }
    
    const labels = [...history.map(h => h.month), ...forecast.map(f => f.month)];
    const actualData = [...history.map(h => h.quantity), ...Array(forecast.length).fill(null)];
    const predictedData = [...Array(history.length).fill(null), ...forecast.map(f => f.predicted_quantity)];
    
    charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual',
                    data: actualData,
                    borderColor: '#E67E22',
                    backgroundColor: 'rgba(230, 126, 34, 0.1)',
                    fill: true
                },
                {
                    label: 'Forecast',
                    data: predictedData,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderDash: [5, 5],
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#a0a0a0' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#3d3d3d' },
                    ticks: { color: '#a0a0a0' }
                },
                x: {
                    grid: { color: '#3d3d3d' },
                    ticks: { color: '#a0a0a0' }
                }
            }
        }
    });
}

// Reports
async function generateReport(type) {
    try {
        let endpoint = '';
        let title = '';
        
        switch (type) {
            case 'inventory':
                endpoint = '/reports/inventory';
                title = 'Inventory Report';
                break;
            case 'sales':
                endpoint = '/reports/sales';
                title = 'Sales Report';
                break;
            case 'expiry':
                endpoint = '/reports/expiry';
                title = 'Expiry Report';
                break;
            case 'forecast':
                endpoint = '/reports/forecast';
                title = 'Forecast Report';
                break;
        }
        
        const response = await apiCall(endpoint);
        const data = await response.json();
        
        document.getElementById('report-output').style.display = 'block';
        document.getElementById('report-title').textContent = title;
        
        // Build table
        const table = document.getElementById('report-table');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');
        
        if (data.data && data.data.length > 0) {
            const headers = Object.keys(data.data[0]);
            thead.innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            tbody.innerHTML = data.data.map(row => 
                '<tr>' + headers.map(h => `<td>${row[h]}</td>`).join('') + '</tr>'
            ).join('');
        } else if (data.items) {
            thead.innerHTML = '<tr><th>Item</th><th>Latest Forecast</th></tr>';
            tbody.innerHTML = data.items.map(item => 
                `<tr><td>${item.name}</td><td>${item.latest_forecast ? item.latest_forecast.predicted_quantity.toFixed(2) : 'N/A'}</td></tr>`
            ).join('');
        } else {
            thead.innerHTML = '<tr><th>Data</th></tr>';
            tbody.innerHTML = '<tr><td>No data available</td></tr>';
        }
        
    } catch (error) {
        console.error('Failed to generate report:', error);
        alert('Failed to generate report');
    }
}

// Admin
async function loadAdminData() {
    try {
        // Load users
        const usersResponse = await apiCall('/admin/users');
        const usersData = await usersResponse.json();
        
        const usersTable = document.getElementById('users-table');
        usersTable.innerHTML = usersData.users.map(user => `
            <tr>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="status-badge active">${user.role}</span></td>
                <td><span class="status-badge ${user.status}">${user.status}</span></td>
                <td>
                    <button class="action-btn" onclick="editUser(${user.id})"><i class="fas fa-edit"></i></button>
                    ${user.status === 'active' ? 
                        `<button class="action-btn danger" onclick="deactivateUser(${user.id})"><i class="fas fa-ban"></i></button>` :
                        `<button class="action-btn" onclick="activateUser(${user.id})"><i class="fas fa-check"></i></button>`
                    }
                </td>
            </tr>
        `).join('');
        
        // Load activity logs
        const logsResponse = await apiCall('/admin/activity-logs?limit=20');
        const logsData = await logsResponse.json();
        
        const logsTable = document.getElementById('activity-logs');
        logsTable.innerHTML = logsData.logs.map(log => `
            <tr>
                <td>${new Date(log.created_at).toLocaleString()}</td>
                <td>${log.user_name || 'System'}</td>
                <td>${log.action}</td>
                <td>${log.details || '-'}</td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Failed to load admin data:', error);
    }
}

function showAddUserModal() {
    const content = `
        <form class="modal-form" onsubmit="saveUser(event)">
            <div class="form-group">
                <label>Name *</label>
                <input type="text" id="user-name-input" required>
            </div>
            <div class="form-group">
                <label>Email *</label>
                <input type="email" id="user-email-input" required>
            </div>
            <div class="form-group">
                <label>Password *</label>
                <input type="password" id="user-password-input" required>
            </div>
            <div class="form-group">
                <label>Role *</label>
                <select id="user-role-input" required>
                    <option value="employee">Employee</option>
                    <option value="admin">Admin</option>
                    <option value="owner">Owner</option>
                </select>
            </div>
            <div class="modal-form-actions">
                <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn-primary">Create User</button>
            </div>
        </form>
    `;
    
    showModal('Add New User', content);
}

async function saveUser(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('user-name-input').value,
        email: document.getElementById('user-email-input').value,
        password: document.getElementById('user-password-input').value,
        role: document.getElementById('user-role-input').value
    };
    
    try {
        const response = await apiCall('/admin/users', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadAdminData();
            alert('User created successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to create user');
        }
    } catch (error) {
        alert('Failed to create user');
    }
}

async function deactivateUser(id) {
    if (!confirm('Are you sure you want to deactivate this user?')) return;
    
    try {
        const response = await apiCall(`/admin/users/${id}`, { method: 'DELETE' });
        
        if (response.ok) {
            loadAdminData();
            alert('User deactivated successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to deactivate user');
        }
    } catch (error) {
        alert('Failed to deactivate user');
    }
}

async function activateUser(id) {
    try {
        const response = await apiCall(`/admin/users/${id}/activate`, { method: 'POST' });
        
        if (response.ok) {
            loadAdminData();
            alert('User activated successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to activate user');
        }
    } catch (error) {
        alert('Failed to activate user');
    }
}

// Modal helpers
function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-content').innerHTML = content;
    document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal-overlay')) {
        closeModal();
    }
});
