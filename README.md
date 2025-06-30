# Sales Management System - Master-Slave PostgreSQL Implementation

This repository provides a comprehensive implementation of a **Sales Management System** using **PostgreSQL master-slave replication** with **Change Data Capture (CDC)** and **RisingWave**. The system demonstrates real-world clean architecture patterns with a modern **Streamlit** dashboard for data management and analytics.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                          │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │   Data Management   │  │     Analytics Dashboard        │   │
│  │   (CRUD Operations) │  │     (Real-time Reports)        │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Services Layer                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Sales Service (Business Logic)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Repository Layer                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Sales Repository (Data Access)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Database Layer                                │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │   Master Database    │    │      Slave Database          │   │
│  │   (Write Operations) │◄──►│    (Read Operations)         │   │
│  │   - INSERT           │    │    - SELECT                  │   │
│  │   - UPDATE           │    │    - Analytics Queries       │   │
│  │   - DELETE           │    │                              │   │
│  └──────────────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### Core Features

- **Master-Slave Database Pattern**: Write operations go to master, read operations from slave
- **Clean Architecture**: Separation of concerns with proper layering
- **Real-time Analytics**: Live dashboard with sales metrics and trends
- **CRUD Operations**: Complete Create, Read, Update, Delete functionality
- **Data Validation**: Comprehensive input validation and error handling
- **Sample Data Generation**: Built-in fake data generator for testing

### Dashboard Features

- **📊 Data Management Interface**

  - View transactions and sales items
  - Add new transactions with multiple items
  - Edit existing transactions and items
  - Delete operations with confirmation
  - Paginated data display

- **📈 Analytics Dashboard**
  - Key performance metrics (revenue, transactions, items sold)
  - Sales trend charts (daily revenue over time)
  - Top products analysis
  - Recent transactions overview
  - Interactive Plotly charts

### Technical Features

- **Containerized Database**: Docker setup for PostgreSQL master-slave
- **Connection Pooling**: Efficient database connection management
- **Error Handling**: Comprehensive error handling and logging
- **Environment Configuration**: Flexible configuration via environment variables
- **Type Safety**: Pydantic models for data validation

## 📦 Project Structure

```
src/
├── config/
│   ├── __init__.py
│   └── settings.py           # Application configuration
├── database/
│   ├── __init__.py
│   └── manager.py            # Database connection manager
├── models/
│   ├── __init__.py
│   └── sales.py              # Pydantic data models
├── repositories/
│   ├── __init__.py
│   ├── interfaces.py         # Repository interfaces
│   └── sales_repository.py   # Sales data access layer
├── services/
│   ├── __init__.py
│   └── sales_service.py      # Business logic layer
├── streamlit_app/
│   ├── .streamlit/
│   │   └── config.toml       # Streamlit configuration
│   └── main.py               # Streamlit dashboard
├── utils/
│   ├── __init__.py
│   ├── helpers.py            # Utility functions
│   └── sample_data.py        # Sample data generator
├── main.py                   # Application entry point
└── requirements.txt          # Python dependencies
```

## 🗄️ Database Schema

The system uses two main tables for sales transaction management:

### Sales Transaction Table

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

### Sales Item Table

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
- ✅ Launch the Streamlit application

---

## ⚡ Quick Start (Simple Way)

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

3. **Run the Application**

   ```bash
   python run.py
   ```

   The script will:

   - Automatically check and install missing dependencies
   - Initialize the database tables
   - Start the Streamlit application at `http://localhost:8501`

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

## 🔍 Key Components

### Database Manager (`database/manager.py`)

- Manages connection pools for master and slave databases
- Provides context managers for safe connection handling
- Implements read/write operation routing

### Sales Service (`services/sales_service.py`)

- Contains business logic for sales operations
- Handles transaction calculations and validations
- Provides high-level API for the presentation layer

### Sales Repository (`repositories/sales_repository.py`)

- Implements data access patterns
- Executes SQL queries with proper parameter binding
- Handles database-specific operations

### Streamlit Dashboard (`streamlit_app/main.py`)

- Modern web interface for data management
- Interactive charts and visualizations
- Real-time data updates and form handling

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
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section below
2. Open an issue on GitHub
3. Review the logs in `app.log`

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Check if Docker services are running
docker-compose ps

# Restart database services
./run.sh stop
./run.sh docker

# Check database logs
docker-compose logs postgres-master
docker-compose logs postgres-slave
```

### Python Dependencies Issues

```bash
# Recreate virtual environment
./run.sh clean
./run.sh setup
```

### Port Conflicts

If ports 5676, 5677, or 8501 are in use, modify the `.env` file or `docker-compose.yml` accordingly.

---

**Built with ❤️ using Python, PostgreSQL, Streamlit, and Docker**
