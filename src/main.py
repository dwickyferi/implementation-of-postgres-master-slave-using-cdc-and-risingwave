#!/usr/bin/env python3
"""
Master-Slave PostgreSQL Implementation with Real-time Dashboard

This is a complete master-slave PostgreSQL implementation that demonstrates:
- Master-Slave PostgreSQL pattern
- Clean Architecture with proper layering
- Real-time analytics dashboard
- CRUD operations for sales data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from faker import Faker
import random
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# ========================================
# CONFIGURATION
# ========================================

class DatabaseConfig:
    """Database configuration"""
    def __init__(self, host, port, name, user, password):
        self.host = host
        self.port = port
        self.name = name
        self.user = user
        self.password = password
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

# Database configurations
MASTER_DB = DatabaseConfig(
    host=os.getenv("MASTER_DB_HOST", "localhost"),
    port=int(os.getenv("MASTER_DB_PORT", 5676)),
    name=os.getenv("MASTER_DB_NAME", "postgres"),
    user=os.getenv("MASTER_DB_USER", "postgres"),
    password=os.getenv("MASTER_DB_PASSWORD", "postgres")
)

SLAVE_DB = DatabaseConfig(
    host=os.getenv("SLAVE_DB_HOST", "localhost"),
    port=int(os.getenv("SLAVE_DB_PORT", 5677)),
    name=os.getenv("SLAVE_DB_NAME", "postgres"),
    user=os.getenv("SLAVE_DB_USER", "postgres"),
    password=os.getenv("SLAVE_DB_PASSWORD", "postgres")
)

# ========================================
# DATA MODELS
# ========================================

class SalesTransactionBase(BaseModel):
    """Base model for Sales Transaction"""
    transaction_time: datetime
    cashier_id: int
    store_id: int
    payment_method: str
    total_amount: Decimal
    total_discount: Decimal = Decimal('0')
    customer_id: Optional[int] = None

class SalesTransaction(SalesTransactionBase):
    """Full Sales Transaction model"""
    transaction_id: int
    created_at: datetime

class SalesItemBase(BaseModel):
    """Base model for Sales Item"""
    transaction_id: int
    product_code: str
    product_name: str
    category: Optional[str] = None
    quantity: int
    unit_price: Decimal
    discount: Decimal = Decimal('0')
    total_price: Decimal

class SalesItem(SalesItemBase):
    """Full Sales Item model"""
    item_id: int

# ========================================
# DATABASE MANAGER
# ========================================

class DatabaseManager:
    """Database connection manager for master-slave setup"""
    
    def __init__(self):
        self._master_pool: Optional[SimpleConnectionPool] = None
        self._slave_pool: Optional[SimpleConnectionPool] = None
        self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialize connection pools for master and slave databases"""
        try:
            # Master database pool (for write operations)
            self._master_pool = SimpleConnectionPool(
                1, 10,  # min and max connections
                host=MASTER_DB.host,
                port=MASTER_DB.port,
                database=MASTER_DB.name,
                user=MASTER_DB.user,
                password=MASTER_DB.password
            )
            
            # Slave database pool (for read operations)
            self._slave_pool = SimpleConnectionPool(
                1, 10,  # min and max connections
                host=SLAVE_DB.host,
                port=SLAVE_DB.port,
                database=SLAVE_DB.name,
                user=SLAVE_DB.user,
                password=SLAVE_DB.password
            )
            
        except Exception as e:
            st.error(f"Failed to initialize database pools: {e}")
            raise
    
    @contextmanager
    def get_master_connection(self):
        """Get connection from master database pool"""
        if not self._master_pool:
            raise RuntimeError("Master database pool not initialized")
        
        connection = None
        try:
            connection = self._master_pool.getconn()
            connection.autocommit = False
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self._master_pool.putconn(connection)
    
    @contextmanager
    def get_slave_connection(self):
        """Get connection from slave database pool"""
        if not self._slave_pool:
            raise RuntimeError("Slave database pool not initialized")
        
        connection = None
        try:
            connection = self._slave_pool.getconn()
            connection.autocommit = True  # Read-only, autocommit is fine
            yield connection
        except Exception as e:
            raise
        finally:
            if connection:
                self._slave_pool.putconn(connection)
    
    def execute_write_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """Execute write query on master database"""
        with self.get_master_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                conn.commit()
                
                # Return results if it's a returning query
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return None
    
    def execute_read_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute read query on slave database"""
        with self.get_slave_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_read_query_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Execute read query and return single result"""
        with self.get_slave_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def check_connection(self) -> Dict[str, bool]:
        """Check database connections"""
        status = {"master": False, "slave": False}
        
        try:
            with self.get_master_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    status["master"] = True
        except Exception:
            pass
        
        try:
            with self.get_slave_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    status["slave"] = True
        except Exception:
            pass
        
        return status
    
    def create_tables(self):
        """Create tables if they don't exist"""
        create_sales_transaction_table = """
        CREATE TABLE IF NOT EXISTS sales_transaction (
            transaction_id SERIAL PRIMARY KEY,
            transaction_time TIMESTAMP NOT NULL,
            cashier_id INT NOT NULL,
            store_id INT NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            total_amount NUMERIC(12, 2) NOT NULL,
            total_discount NUMERIC(12, 2) DEFAULT 0,
            customer_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_sales_item_table = """
        CREATE TABLE IF NOT EXISTS sales_item (
            item_id SERIAL PRIMARY KEY,
            transaction_id INT REFERENCES sales_transaction(transaction_id) ON DELETE CASCADE,
            product_code VARCHAR(50) NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            quantity INT NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            discount NUMERIC(10, 2) DEFAULT 0,
            total_price NUMERIC(12, 2) NOT NULL
        );
        """
        
        try:
            self.execute_write_query(create_sales_transaction_table)
            self.execute_write_query(create_sales_item_table)
        except Exception as e:
            st.error(f"Failed to create tables: {e}")
            raise

# ========================================
# SERVICES
# ========================================

class SalesService:
    """Business logic layer for sales operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_transaction(self, transaction_data: dict, items_data: List[dict]) -> SalesTransaction:
        """Create a complete transaction with items"""
        try:
            # Calculate totals
            total_amount = Decimal('0')
            total_discount = Decimal('0')
            
            for item_data in items_data:
                unit_price = Decimal(str(item_data['unit_price']))
                quantity = item_data['quantity']
                discount = Decimal(str(item_data.get('discount', 0)))
                
                item_total = (unit_price * quantity) - discount
                total_amount += item_total
                total_discount += discount
            
            # Set calculated totals
            transaction_data['total_amount'] = total_amount
            transaction_data['total_discount'] = total_discount
            
            # Create transaction
            query = """
            INSERT INTO sales_transaction 
            (transaction_time, cashier_id, store_id, payment_method, total_amount, total_discount, customer_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING transaction_id, transaction_time, cashier_id, store_id, payment_method, 
                     total_amount, total_discount, customer_id, created_at
            """
            
            params = (
                transaction_data['transaction_time'],
                transaction_data['cashier_id'],
                transaction_data['store_id'],
                transaction_data['payment_method'],
                transaction_data['total_amount'],
                transaction_data['total_discount'],
                transaction_data.get('customer_id')
            )
            
            result = self.db.execute_write_query(query, params)
            if not result:
                raise Exception("Failed to create transaction")
            
            transaction = SalesTransaction(**result[0])
            
            # Create items
            for item_data in items_data:
                item_data['transaction_id'] = transaction.transaction_id
                
                unit_price = Decimal(str(item_data['unit_price']))
                quantity = item_data['quantity']
                discount = Decimal(str(item_data.get('discount', 0)))
                item_data['total_price'] = (unit_price * quantity) - discount
                
                item_query = """
                INSERT INTO sales_item 
                (transaction_id, product_code, product_name, category, quantity, unit_price, discount, total_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                item_params = (
                    item_data['transaction_id'],
                    item_data['product_code'],
                    item_data['product_name'],
                    item_data.get('category'),
                    item_data['quantity'],
                    item_data['unit_price'],
                    item_data['discount'],
                    item_data['total_price']
                )
                
                self.db.execute_write_query(item_query, item_params)
            
            return transaction
            
        except Exception as e:
            raise Exception(f"Failed to create transaction: {e}")
    
    def get_transactions(self, page: int = 1, page_size: int = 20) -> List[SalesTransaction]:
        """Get paginated list of transactions"""
        offset = (page - 1) * page_size
        query = """
        SELECT transaction_id, transaction_time, cashier_id, store_id, payment_method,
               total_amount, total_discount, customer_id, created_at
        FROM sales_transaction 
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        results = self.db.execute_read_query(query, (page_size, offset))
        return [SalesTransaction(**row) for row in results]
    
    def get_transaction(self, transaction_id: int) -> Optional[SalesTransaction]:
        """Get a single transaction"""
        query = """
        SELECT transaction_id, transaction_time, cashier_id, store_id, payment_method,
               total_amount, total_discount, customer_id, created_at
        FROM sales_transaction 
        WHERE transaction_id = %s
        """
        
        result = self.db.execute_read_query_one(query, (transaction_id,))
        return SalesTransaction(**result) if result else None
    
    def get_items_by_transaction(self, transaction_id: int) -> List[SalesItem]:
        """Get all items for a transaction"""
        query = """
        SELECT item_id, transaction_id, product_code, product_name, category,
               quantity, unit_price, discount, total_price
        FROM sales_item 
        WHERE transaction_id = %s
        ORDER BY item_id
        """
        
        results = self.db.execute_read_query(query, (transaction_id,))
        return [SalesItem(**row) for row in results]
    
    def update_transaction(self, transaction_id: int, update_data: dict) -> Optional[SalesTransaction]:
        """Update a transaction"""
        query = """
        UPDATE sales_transaction 
        SET transaction_time = %s, cashier_id = %s, store_id = %s, 
            payment_method = %s, total_amount = %s, customer_id = %s
        WHERE transaction_id = %s
        RETURNING transaction_id, transaction_time, cashier_id, store_id, payment_method,
                 total_amount, total_discount, customer_id, created_at
        """
        
        params = (
            update_data['transaction_time'],
            update_data['cashier_id'],
            update_data['store_id'],
            update_data['payment_method'],
            update_data['total_amount'],
            update_data.get('customer_id'),
            transaction_id
        )
        
        result = self.db.execute_write_query(query, params)
        if result and len(result) > 0:
            return SalesTransaction(**result[0])
        return None
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        try:
            query = "DELETE FROM sales_transaction WHERE transaction_id = %s"
            self.db.execute_write_query(query, (transaction_id,))
            return True
        except Exception:
            return False
    
    def get_sales_stats(self) -> dict:
        """Get sales statistics"""
        query = """
        SELECT 
            COUNT(DISTINCT st.transaction_id) as total_transactions,
            COALESCE(SUM(st.total_amount), 0) as total_revenue,
            COALESCE(SUM(si.quantity), 0) as total_items_sold,
            COALESCE(AVG(st.total_amount), 0) as average_transaction_value
        FROM sales_transaction st
        LEFT JOIN sales_item si ON st.transaction_id = si.transaction_id
        """
        
        result = self.db.execute_read_query_one(query)
        if result:
            return {
                "total_transactions": result['total_transactions'] or 0,
                "total_revenue": float(result['total_revenue'] or 0),
                "total_items_sold": result['total_items_sold'] or 0,
                "average_transaction_value": float(result['average_transaction_value'] or 0)
            }
        
        return {
            "total_transactions": 0,
            "total_revenue": 0.0,
            "total_items_sold": 0,
            "average_transaction_value": 0.0
        }
    
    def get_top_products(self, limit: int = 10) -> List[dict]:
        """Get top selling products"""
        query = """
        SELECT 
            product_name,
            SUM(quantity) as total_quantity,
            SUM(total_price) as total_revenue
        FROM sales_item
        GROUP BY product_name
        ORDER BY total_quantity DESC
        LIMIT %s
        """
        
        return self.db.execute_read_query(query, (limit,))
    
    def get_sales_trend(self, days: int = 30) -> List[dict]:
        """Get sales trend data"""
        query = """
        SELECT 
            DATE(transaction_time) as date,
            SUM(total_amount) as total_amount,
            COUNT(*) as transaction_count
        FROM sales_transaction
        WHERE transaction_time >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY DATE(transaction_time)
        ORDER BY date
        """
        
        return self.db.execute_read_query(query, (days,))

# ========================================
# SAMPLE DATA GENERATOR
# ========================================

def generate_sample_data(num_transactions: int = 10) -> List[dict]:
    """Generate sample transaction data"""
    fake = Faker()
    
    products = [
        {'code': 'P001', 'name': 'Coffee - Americano', 'category': 'Beverages'},
        {'code': 'P002', 'name': 'Coffee - Latte', 'category': 'Beverages'},
        {'code': 'P003', 'name': 'Sandwich - Ham & Cheese', 'category': 'Food'},
        {'code': 'P004', 'name': 'Croissant - Plain', 'category': 'Food'},
        {'code': 'P005', 'name': 'Muffin - Blueberry', 'category': 'Food'},
        {'code': 'P006', 'name': 'Tea - Green', 'category': 'Beverages'},
        {'code': 'P007', 'name': 'Juice - Orange', 'category': 'Beverages'},
        {'code': 'P008', 'name': 'Salad - Caesar', 'category': 'Food'},
        {'code': 'P009', 'name': 'Cake - Chocolate', 'category': 'Desserts'},
        {'code': 'P010', 'name': 'Cookie - Chocolate Chip', 'category': 'Desserts'},
    ]
    
    payment_methods = ['Cash', 'Credit Card', 'Debit Card', 'Digital Wallet', 'Bank Transfer']
    
    sample_data = []
    
    for _ in range(num_transactions):
        transaction = {
            'transaction_time': fake.date_time_between(start_date='-30d', end_date='now'),
            'cashier_id': random.randint(1, 10),
            'store_id': random.randint(1, 5),
            'payment_method': random.choice(payment_methods),
            'customer_id': random.randint(1, 1000) if random.choice([True, False]) else None
        }
        
        # Generate 1-5 items per transaction
        num_items = random.randint(1, 5)
        items = []
        
        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 5)
            unit_price = round(random.uniform(2.0, 25.0), 2)
            discount = round(random.uniform(0.0, 5.0), 2)
            
            items.append({
                'product_code': product['code'],
                'product_name': product['name'],
                'category': product['category'],
                'quantity': quantity,
                'unit_price': unit_price,
                'discount': discount
            })
        
        sample_data.append({
            'transaction': transaction,
            'items': items
        })
    
    return sample_data

# ========================================
# UTILITY FUNCTIONS
# ========================================

def format_currency(amount: float) -> str:
    """Format currency with commas and 2 decimal places"""
    return f"${amount:,.2f}"

def format_number(number: int) -> str:
    """Format number with commas"""
    return f"{number:,}"

# ========================================
# STREAMLIT APPLICATION
# ========================================

# Page configuration
st.set_page_config(
    page_title="Mater Slave PostgreSQL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stTab [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTab [data-baseweb="tab"] {
        padding-left: 12px;
        padding-right: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database manager and service
@st.cache_resource
def get_database_manager():
    """Get database manager instance"""
    return DatabaseManager()

@st.cache_resource
def get_sales_service():
    """Get sales service instance"""
    db_manager = get_database_manager()
    return SalesService(db_manager)

def main():
    """Main Streamlit application"""
    st.title("📊 Master Slave Postgres")
    st.markdown("**Master-Slave PostgreSQL Implementation with Real-time Analytics**")
    
    # Initialize services
    try:
        db_manager = get_database_manager()
        sales_service = get_sales_service()
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        st.stop()
    
    # Sidebar for navigation and status
    with st.sidebar:
        st.header("🔧 System Status")
        
        # Database connection status
        status = db_manager.check_connection()
        
        col1, col2 = st.columns(2)
        with col1:
            if status["master"]:
                st.success("Master ✅")
            else:
                st.error("Master ❌")
        with col2:
            if status["slave"]:
                st.success("Slave ✅")
            else:
                st.error("Slave ❌")
        
        st.divider()
        
        # Initialize database button
        if st.button("🔄 Initialize Database", use_container_width=True):
            try:
                db_manager.create_tables()
                st.success("Database tables initialized successfully!")
            except Exception as e:
                st.error(f"Failed to initialize database: {e}")
        
        # Generate sample data button
        if st.button("📝 Generate Sample Data", use_container_width=True):
            try:
                with st.spinner("Generating sample data..."):
                    sample_data = generate_sample_data(10)
                    
                    for data in sample_data:
                        sales_service.create_transaction(
                            data['transaction'], data['items']
                        )
                    
                    st.success("Generated 10 sample transactions!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error generating sample data: {e}")
    
    # Main navigation tabs
    tab1, tab2 = st.tabs(["📋 Data Management", "📈 Analytics Dashboard"])
    
    with tab1:
        data_management_page(sales_service)
    
    with tab2:
        analytics_dashboard_page(sales_service)

def data_management_page(sales_service):
    """Data management interface"""
    st.header("📋 Data Management")
    
    # Sub-tabs for different operations
    subtab1, subtab2, subtab3, subtab4 = st.tabs(["📊 View Data", "➕ Add Transaction", "✏️ Edit Data", "🗑️ Delete Data"])
    
    with subtab1:
        view_data_section(sales_service)
    
    with subtab2:
        add_transaction_section(sales_service)
    
    with subtab3:
        edit_data_section(sales_service)
    
    with subtab4:
        delete_data_section(sales_service)

def view_data_section(sales_service):
    """View data section"""
    st.subheader("📊 View Sales Data")
    
    # Data type selection
    data_type = st.selectbox("Select data to view:", ["Transactions", "Transaction with Items"])
    
    if data_type == "Transactions":
        try:
            # Pagination controls
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                page = st.number_input("Page", min_value=1, value=1)
            with col2:
                page_size = st.selectbox("Items per page", [10, 20, 50, 100], index=1)
            
            transactions = sales_service.get_transactions(page=page, page_size=page_size)
            
            if transactions:
                # Convert to DataFrame for display
                df_data = []
                for transaction in transactions:
                    df_data.append({
                        "ID": transaction.transaction_id,
                        "Date": transaction.transaction_time.strftime("%Y-%m-%d %H:%M"),
                        "Cashier ID": transaction.cashier_id,
                        "Store ID": transaction.store_id,
                        "Payment Method": transaction.payment_method,
                        "Total Amount": format_currency(float(transaction.total_amount)),
                        "Discount": format_currency(float(transaction.total_discount)),
                        "Customer ID": transaction.customer_id or "N/A"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No transactions found.")
        
        except Exception as e:
            st.error(f"Error loading transactions: {e}")
    
    elif data_type == "Transaction with Items":
        try:
            transaction_id = st.number_input("Transaction ID", min_value=1)
            
            if st.button("Load Transaction", key="load_transaction_details"):
                transaction = sales_service.get_transaction(transaction_id)
                
                if transaction:
                    # Display transaction details
                    st.subheader("Transaction Details")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Transaction ID", transaction.transaction_id)
                    with col2:
                        st.metric("Total Amount", format_currency(float(transaction.total_amount)))
                    with col3:
                        st.metric("Payment Method", transaction.payment_method)
                    with col4:
                        st.metric("Store ID", transaction.store_id)
                    
                    # Display items
                    st.subheader("Items")
                    items = sales_service.get_items_by_transaction(transaction_id)
                    
                    if items:
                        df_data = []
                        for item in items:
                            df_data.append({
                                "Product": item.product_name,
                                "Code": item.product_code,
                                "Category": item.category or "N/A",
                                "Quantity": item.quantity,
                                "Unit Price": format_currency(float(item.unit_price)),
                                "Total": format_currency(float(item.total_price))
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No items found for this transaction.")
                else:
                    st.error("Transaction not found.")
        
        except Exception as e:
            st.error(f"Error loading transaction: {e}")

def add_transaction_section(sales_service):
    """Add new transaction"""
    st.subheader("➕ Add New Transaction")
    
    # Dynamic item addition (outside of form)
    # Initialize or reset items if corrupted
    if 'items' not in st.session_state or not isinstance(st.session_state.items, list):
        st.session_state.items = []
    
    # Add item section (outside of form)
    with st.expander("Add Item"):
        item_col1, item_col2 = st.columns(2)
        with item_col1:
            product_code = st.text_input("Product Code", key="add_product_code")
            product_name = st.text_input("Product Name", key="add_product_name")
            category = st.text_input("Category (optional)", key="add_category")
        
        with item_col2:
            quantity = st.number_input("Quantity", min_value=1, value=1, key="add_quantity")
            unit_price = st.number_input("Unit Price", min_value=0.01, value=1.00, step=0.01, key="add_unit_price")
            discount = st.number_input("Discount", min_value=0.00, value=0.00, step=0.01, key="add_discount")
        
        if st.button("Add Item", key="add_item_button"):
            if product_code and product_name:
                item = {
                    'product_code': product_code,
                    'product_name': product_name,
                    'category': category if category else None,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount': discount
                }
                # Ensure items is a list before appending
                if not isinstance(st.session_state.items, list):
                    st.session_state.items = []
                st.session_state.items.append(item)
                st.success("Item added!")
                st.rerun()
            else:
                st.error("Product code and name are required!")
    
    # Display current items (outside of form)
    try:
        if st.session_state.items and isinstance(st.session_state.items, list):
            st.write("**Current Items:**")
            
            # Create column headers
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            col1.write("**Product**")
            col2.write("**Qty**")
            col3.write("**Price**")
            col4.write("**Discount**")
            col5.write("**Action**")
            
            # Display each item
            for i, item in enumerate(st.session_state.items):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                col1.write(item['product_name'])
                col2.write(str(item['quantity']))
                col3.write(f"${item['unit_price']:.2f}")
                col4.write(f"${item['discount']:.2f}")
                
                # Use unique key based on item details and index
                unique_key = f"remove_item_{i}_{item['product_code']}_{item['product_name']}"
                if col5.button("🗑️", key=unique_key, help=f"Remove {item['product_name']}"):
                    st.session_state.items.pop(i)
                    st.rerun()
                    
            # Show total
            if st.session_state.items:
                total = sum((item['unit_price'] * item['quantity']) - item['discount'] for item in st.session_state.items)
                st.write(f"**Total: ${total:.2f}**")
                
    except (TypeError, AttributeError, KeyError) as e:
        st.warning("Items list was corrupted. Resetting...")
        st.session_state.items = []
        st.rerun()
    
    # Transaction form
    with st.form("add_transaction_form"):
        st.write("**Transaction Details**")
        
        col1, col2 = st.columns(2)
        with col1:
            cashier_id = st.number_input("Cashier ID", min_value=1, value=1)
            store_id = st.number_input("Store ID", min_value=1, value=1)
            payment_method = st.selectbox("Payment Method", 
                                        ["Cash", "Credit Card", "Debit Card", "Digital Wallet", "Bank Transfer"])
        
        with col2:
            transaction_time = st.date_input("Transaction Time", value=datetime.now())
            customer_id = st.number_input("Customer ID (optional)", min_value=0, value=0)
            customer_id = customer_id if customer_id > 0 else None
        
        # Submit transaction
        submitted = st.form_submit_button("Create Transaction", type="primary")
        
        if submitted:
            try:
                if not st.session_state.items:
                    st.error("Please add at least one item!")
                else:
                    # Prepare transaction data
                    transaction_data = {
                        'transaction_time': transaction_time,
                        'cashier_id': cashier_id,
                        'store_id': store_id,
                        'payment_method': payment_method,
                        'customer_id': customer_id
                    }
                    
                    # Create transaction
                    transaction = sales_service.create_transaction(
                        transaction_data, st.session_state.items
                    )
                    
                    st.success(f"Transaction created successfully! ID: {transaction.transaction_id}")
                    st.session_state.items = []  # Clear items
                    st.rerun()
            
            except Exception as e:
                st.error(f"Error creating transaction: {e}")

def edit_data_section(sales_service):
    """Edit existing data"""
    st.subheader("✏️ Edit Transaction")
    
    transaction_id = st.number_input("Transaction ID to edit", min_value=1)
    
    if st.button("Load Transaction", key="load_transaction_edit"):
        try:
            transaction = sales_service.get_transaction(transaction_id)
            if transaction:
                st.session_state.edit_transaction = transaction
                st.success("Transaction loaded!")
            else:
                st.error("Transaction not found!")
        except Exception as e:
            st.error(f"Error loading transaction: {e}")
    
    if 'edit_transaction' in st.session_state:
        transaction = st.session_state.edit_transaction
        
        with st.form("edit_transaction_form"):
            col1, col2 = st.columns(2)
            with col1:
                cashier_id = st.number_input("Cashier ID", value=transaction.cashier_id)
                store_id = st.number_input("Store ID", value=transaction.store_id)
                payment_method = st.selectbox("Payment Method", 
                                            ["Cash", "Credit Card", "Debit Card", "Digital Wallet", "Bank Transfer"],
                                            index=["Cash", "Credit Card", "Debit Card", "Digital Wallet", "Bank Transfer"].index(transaction.payment_method))
            
            with col2:
                transaction_time = st.date_input("Transaction Time", value=transaction.transaction_time)
                total_amount = st.number_input("Total Amount", value=float(transaction.total_amount), step=0.01)
                customer_id = st.number_input("Customer ID", value=transaction.customer_id or 0)
                customer_id = customer_id if customer_id > 0 else None
            
            submitted = st.form_submit_button("Update Transaction")
            
            if submitted:
                try:
                    update_data = {
                        'transaction_time': transaction_time,
                        'cashier_id': cashier_id,
                        'store_id': store_id,
                        'payment_method': payment_method,
                        'total_amount': total_amount,
                        'customer_id': customer_id
                    }
                    
                    updated_transaction = sales_service.update_transaction(transaction_id, update_data)
                    if updated_transaction:
                        st.success("Transaction updated successfully!")
                        del st.session_state.edit_transaction
                        st.rerun()
                    else:
                        st.error("Failed to update transaction!")
                
                except Exception as e:
                    st.error(f"Error updating transaction: {e}")

def delete_data_section(sales_service):
    """Delete data section"""
    st.subheader("🗑️ Delete Transaction")
    
    transaction_id = st.number_input("Transaction ID to delete", min_value=1)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Delete Transaction", type="secondary", key="delete_transaction_button"):
            if st.session_state.get('confirm_delete_transaction', False):
                try:
                    success = sales_service.delete_transaction(transaction_id)
                    if success:
                        st.success("Transaction deleted successfully!")
                        st.session_state.confirm_delete_transaction = False
                    else:
                        st.error("Failed to delete transaction!")
                except Exception as e:
                    st.error(f"Error deleting transaction: {e}")
            else:
                st.warning("Click again to confirm deletion!")
                st.session_state.confirm_delete_transaction = True
    
    with col2:
        st.warning("⚠️ **Warning**: Deleting a transaction will also delete all associated items!")

def analytics_dashboard_page(sales_service):
    """Analytics dashboard"""
    st.header("📈 Analytics Dashboard")
    
    try:
        # Get dashboard data
        stats = sales_service.get_sales_stats()
        top_products = sales_service.get_top_products(10)
        sales_trend = sales_service.get_sales_trend(30)
        recent_transactions = sales_service.get_transactions(page=1, page_size=10)
        
        # Key metrics
        st.subheader("📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Transactions",
                format_number(stats['total_transactions'])
            )
        
        with col2:
            st.metric(
                "Total Revenue",
                format_currency(stats['total_revenue'])
            )
        
        with col3:
            st.metric(
                "Items Sold",
                format_number(stats['total_items_sold'])
            )
        
        with col4:
            st.metric(
                "Avg Transaction",
                format_currency(stats['average_transaction_value'])
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Sales trend chart
            st.subheader("📈 Sales Trend (Last 30 Days)")
            if sales_trend:
                df_trend = pd.DataFrame([
                    {
                        'Date': trend['date'],
                        'Revenue': float(trend['total_amount']),
                        'Transactions': trend['transaction_count']
                    }
                    for trend in sales_trend
                ])
                
                fig = px.line(df_trend, x='Date', y='Revenue', 
                            title='Daily Revenue Trend',
                            labels={'Revenue': 'Revenue ($)'})
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sales trend data available.")
        
        with col2:
            # Top products chart
            st.subheader("🏆 Top Products")
            if top_products:
                df_products = pd.DataFrame([
                    {
                        'Product': product['product_name'],
                        'Quantity': product['total_quantity'],
                        'Revenue': float(product['total_revenue'])
                    }
                    for product in top_products[:10]
                ])
                
                fig = px.bar(df_products, x='Quantity', y='Product', 
                           orientation='h',
                           title='Top 10 Products by Quantity')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No top products data available.")
        
        # Recent transactions
        st.subheader("🕒 Recent Transactions")
        if recent_transactions:
            df_recent = pd.DataFrame([
                {
                    'ID': t.transaction_id,
                    'Date': t.transaction_time.strftime("%Y-%m-%d %H:%M"),
                    'Amount': format_currency(float(t.total_amount)),
                    'Payment': t.payment_method,
                    'Store': t.store_id
                }
                for t in recent_transactions
            ])
            st.dataframe(df_recent, use_container_width=True)
        else:
            st.info("No recent transactions found.")
    
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")

if __name__ == "__main__":
    main()