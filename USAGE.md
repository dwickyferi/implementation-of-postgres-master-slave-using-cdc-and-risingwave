# Sales Management System - Quick Usage Guide

## 🚀 Quickest Way to Start

1. Make sure Docker is running
2. Run this single command:
   ```bash
   python setup.py
   ```

## 🔧 Manual Start (3 steps)

1. Start databases:

   ```bash
   docker-compose up -d postgres-master postgres-slave
   ```

2. Go to src folder:

   ```bash
   cd src
   ```

3. Run the app:
   ```bash
   python run.py
   ```

## 📱 What You'll See

After running, your browser will open to `http://localhost:8501` with:

### 📊 Data Management Tab

- **View Data**: See transactions and items
- **Add Transaction**: Create new sales with multiple items
- **Edit Data**: Modify existing transactions
- **Delete Data**: Remove transactions (with confirmation)

### 📈 Analytics Dashboard Tab

- **Key Metrics**: Total revenue, transactions, items sold
- **Sales Trends**: Daily revenue charts
- **Top Products**: Best selling items
- **Recent Activity**: Latest transactions

## 🎯 Key Features Demonstrated

### Master-Slave Pattern

- ✍️ **Write Operations** (Add/Edit/Delete) → Master Database (Port 5676)
- 📖 **Read Operations** (View/Analytics) → Slave Database (Port 5677)

### Sample Data

- Click "Generate Sample Data" in sidebar to create test transactions
- Includes realistic products: coffee, sandwiches, desserts
- Various payment methods and customer data

## 🛠️ Requirements

### Minimal Requirements

```
streamlit
psycopg2-binary
pandas
plotly
pydantic
faker
python-dotenv
```

### System Requirements

- Python 3.8+
- Docker & Docker Compose
- 4GB RAM recommended

## 📝 Database Schema

Two main tables:

- `sales_transaction`: Transaction headers
- `sales_item`: Individual items per transaction

All automatically created when you first run the app!

## 🔍 Architecture Highlights

- **Single File Solution**: Everything in `src/main.py` (1000+ lines)
- **Clean Architecture**: Models → Services → Repository → Database
- **Type Safety**: Pydantic models for data validation
- **Connection Pooling**: Efficient database connections
- **Real-time Analytics**: Live charts and metrics

## 🎉 Perfect for Learning

This project demonstrates:

- Master-slave database patterns
- Clean architecture in Python
- Streamlit for rapid web app development
- PostgreSQL with Docker
- Real-world CRUD operations
- Data visualization with Plotly
