# Master-Slave PostgreSQL Implementation with RisingWave

This repository demonstrates a complete **PostgreSQL master-slave replication** implementation using **Change Data Capture (CDC)** and **RisingWave**. The project showcases real-world database architecture patterns with a practical example using a sales data scenario, featuring a **Streamlit** dashboard for demonstrating read/write operation separation and real-time data analytics.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                          │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │   Write Operations  │  │     Read Operations             │   │
│  │   (Master DB)       │  │     (Slave DB)                 │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Application Layer (Clean Architecture)           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Business Logic & Connection Management                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Database Layer                                │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │   Master Database    │    │      Slave Database          │   │
│  │   (Write Operations) │───►│    (Read Operations)         │   │
│  │   - INSERT           │    │    - SELECT                  │   │
│  │   - UPDATE           │    │    - Analytics Queries       │   │
│  │   - DELETE           │    │    - Dashboard Data          │   │
│  │   Port: 5676         │    │    Port: 5677                │   │
│  └──────────────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RisingWave & CDC                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Real-time Data Processing & Change Data Capture           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### Core Database Features

- **Master-Slave PostgreSQL Pattern**: Demonstrates proper separation of write and read operations
- **Change Data Capture (CDC)**: Real-time data synchronization using Debezium
- **RisingWave Integration**: Stream processing for real-time analytics
- **Connection Pooling**: Efficient database connection management
- **Clean Architecture**: Proper separation of concerns and layered design
- **Docker Containerization**: Easy deployment with Docker Compose

### Demo Application Features

- **📊 Write Operations Interface**

  - Create transactions and items (routed to Master DB)
  - Update existing records (routed to Master DB)
  - Delete operations with confirmation (routed to Master DB)
  - Input validation and error handling

- **📈 Read Operations Interface**
  - View transactions and analytics (routed to Slave DB)
  - Real-time dashboard with metrics
  - Interactive charts and visualizations
  - Paginated data display

### Technical Implementation

- **Database Separation**: Clear write/read operation routing
- **Environment Configuration**: Flexible configuration via environment variables
- **Error Handling**: Comprehensive error handling and recovery
- **Type Safety**: Pydantic models for data validation
- **Sample Data Generation**: Built-in data generator for testing replication

## 📦 Project Structure

```
├── docker-compose.yml        # Docker services configuration
├── .env                      # Environment variables
├── README.md                 # Project documentation
├── USAGE.md                  # Quick usage guide
├── setup.py                  # Automated setup script
└── src/
    ├── main.py              # Complete Streamlit application (master-slave demo)
    ├── run.py               # Application runner script
    ├── requirements.txt     # Python dependencies
    └── __init__.py          # Package initialization
```

### Key Files

- **`main.py`**: Complete implementation demonstrating master-slave pattern
- **`run.py`**: Simple runner script for starting the Streamlit application
- **`docker-compose.yml`**: PostgreSQL master-slave setup with RisingWave
- **`.env`**: Database connection configurations

## 🗄️ Database Schema

The demo uses a simple transaction-based schema to demonstrate master-slave operations:

### Sales Transaction Table (Master DB - Writes)

```sql
CREATE TABLE sales_transaction (
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
```

### Sales Item Table (Master DB - Writes)

```sql
CREATE TABLE sales_item (
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
```

### Database Operations Flow

- **Master Database (Port 5676)**: All INSERT, UPDATE, DELETE operations
- **Slave Database (Port 5677)**: All SELECT operations for analytics and reporting
- **CDC**: Changes automatically replicated from master to slave

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Git

## ⚡ Super Quick Start (1 Command)

```bash
python setup.py
```

This single command will:

- ✅ Check Docker installation
- ✅ Start PostgreSQL master-slave databases
- ✅ Install Python dependencies
- ✅ Launch the Streamlit application demonstrating master-slave operations

---

## ⚡ Quick Start (Recommended Method)

### Prerequisites

- Python 3.8+
- Docker & Docker Compose

### 3 Simple Steps to Run

1. **Start Database Services**

   ```bash
   docker-compose up -d postgres-master postgres-slave
   ```

2. **Navigate to Source Directory**

   ```bash
   cd src
   ```

3. **Run the Demo Application**

   ```bash
   python run.py
   ```

   The `run.py` script will:

   - ✅ Automatically check and install missing dependencies
   - ✅ Initialize the database tables on both master and slave
   - ✅ Start the Streamlit application at `http://localhost:8501`
   - ✅ Open your browser automatically to the demo interface

### Alternative Direct Method

```bash
# Install dependencies manually (if needed)
pip install -r src/requirements.txt

# Run the main application
cd src
streamlit run main.py
```

## 📦 What's Included

The complete system is contained in a **single main.py file** (1000+ lines) that includes:

- Database connection management (master-slave pattern)
- Data models and validation
- Business logic services
- Complete Streamlit web interface
- Sample data generator
- Real-time analytics dashboard

## 🔧 Simple Configuration

Database connections can be configured via environment variables in `.env`:

```bash
# Master Database (Write Operations)
MASTER_DB_HOST=localhost
MASTER_DB_PORT=5676
MASTER_DB_USER=postgres
MASTER_DB_PASSWORD=postgres

# Slave Database (Read Operations)
SLAVE_DB_HOST=localhost
SLAVE_DB_PORT=5677
SLAVE_DB_USER=postgres
SLAVE_DB_PASSWORD=postgres
```

## 🎯 Usage Examples

### Adding a New Transaction

1. Navigate to "Data Management" → "Add Transaction"
2. Fill in transaction details (cashier ID, store ID, payment method)
3. Add one or more items with product details
4. Click "Create Transaction"

### Viewing Analytics

1. Navigate to "Analytics Dashboard"
2. View key metrics (total revenue, transactions, items sold)
3. Analyze sales trends and top products
4. Check recent transaction activity

### Master-Slave Verification

The system automatically routes:

- **Write operations** (INSERT, UPDATE, DELETE) → Master Database
- **Read operations** (SELECT, Analytics) → Slave Database

## 🧪 Testing with Sample Data

The system includes a built-in sample data generator that creates realistic sales transactions:

```python
# Generate 20 sample transactions
python main.py sample-data
```

Sample data includes:

- Realistic product names and categories (coffee, food, desserts)
- Random transaction times within the last 30 days
- Various payment methods
- Multiple items per transaction
- Proper price calculations with discounts

## 🐳 Docker Services

The `docker-compose.yml` includes:

- **postgres-master**: Master database (port 5676)
- **postgres-slave**: Slave database (port 5677)
- **RisingWave components**: For CDC and stream processing
- **Prometheus**: For monitoring and metrics
- **MinIO**: For object storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)

## 🎯 Learning Objectives

This implementation demonstrates:

- **Master-Slave Database Architecture**: Proper separation of read and write operations
- **Change Data Capture (CDC)**: Real-time data synchronization patterns
- **RisingWave Integration**: Stream processing for real-time analytics
- **Clean Code Architecture**: Proper layering and separation of concerns
- **Docker Containerization**: Production-ready deployment patterns
- **Connection Management**: Efficient database connection pooling
- **Error Handling**: Robust error handling and recovery mechanisms

## � Key Implementation Details

### Database Routing Logic

```python
# Write operations (INSERT, UPDATE, DELETE) → Master DB
def execute_write_query(self, query: str, params: Optional[tuple] = None):
    with self.get_master_connection() as conn:
        # All write operations go to master database (port 5676)

# Read operations (SELECT) → Slave DB
def execute_read_query(self, query: str, params: Optional[tuple] = None):
    with self.get_slave_connection() as conn:
        # All read operations go to slave database (port 5677)
```

### Connection Pool Configuration

- **Master DB (Port 5676)**: Optimized for write operations with transaction support
- **Slave DB (Port 5677)**: Optimized for read operations with autocommit enabled
- **Connection Pooling**: SimpleConnectionPool for efficient resource management

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Check if Docker services are running
docker-compose ps

# Restart database services
docker-compose up -d postgres-master postgres-slave

# Check database logs
docker-compose logs postgres-master
docker-compose logs postgres-slave
```

### Application Issues

```bash
# Navigate to src directory and run directly
cd src
python run.py

# Or run Streamlit manually
cd src
streamlit run main.py --server.port 8501
```

### Port Conflicts

If ports 5676, 5677, or 8501 are in use, modify the `.env` file accordingly:

```bash
# Edit .env file
MASTER_DB_PORT=5676  # Change if needed
SLAVE_DB_PORT=5677   # Change if needed
```

---

**Built with ❤️ for demonstrating PostgreSQL Master-Slave Architecture with RisingWave**
