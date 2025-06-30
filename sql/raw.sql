-- Step In Postgres Database
-- Step 1 : Create table postgres database for sales transactions
-- Tabel Header Transaksi
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

-- Tabel Item Detail per Transaksi
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

-- Step 2 : Insert sample data into sales_transaction and sales_item tables
-- Header Transaksi
INSERT INTO sales_transaction (transaction_time, cashier_id, store_id, payment_method, total_amount, total_discount, customer_id)
VALUES
('2025-06-29 10:15:00', 101, 1, 'Cash', 45000, 5000, 201),
('2025-06-29 11:45:00', 102, 1, 'QRIS', 28000, 0, NULL),
('2025-06-30 08:10:00', 103, 2, 'Debit Card', 65000, 10000, 202);

-- Item Transaksi
INSERT INTO sales_item (transaction_id, product_code, product_name, category, quantity, unit_price, discount, total_price)
VALUES
(1, 'SNK001', 'Potato Chips', 'Snacks', 2, 10000, 2000, 18000),
(1, 'DRK002', 'Mineral Water 600ml', 'Drinks', 1, 7000, 0, 7000),
(1, 'SNK003', 'Chocolate Bar', 'Snacks', 1, 10000, 0, 10000),
(2, 'DRK004', 'Iced Tea Bottle', 'Drinks', 2, 14000, 0, 28000),
(3, 'FDS001', 'Instant Noodles', 'Food', 3, 5000, 0, 15000),
(3, 'SNK001', 'Potato Chips', 'Snacks', 1, 10000, 1000, 9000),
(3, 'DRK005', 'Milk Coffee Can', 'Drinks', 2, 12000, 2000, 22000);


-- Step In RisingWave Database
-- Step 0 : Create RisingWave database
CREATE SOURCE pg_source WITH (
    connector='postgres-cdc',
    hostname='postgres-master',
    port='5432',
    username='postgres',
    password='postgres',
    database.name='postgres',
    schema.name='public',
    slot.name = 'rising_wave',
    publication.name ='rw_publication'
);

-- Step 1 : Create table in RisingWave database for sales transactions
CREATE TABLE sales_transaction (
    transaction_id INT PRIMARY KEY,
    transaction_time TIMESTAMP ,
    cashier_id INT ,
    store_id INT ,
    payment_method VARCHAR,
    total_amount NUMERIC,
    total_discount NUMERIC,
    customer_id INT,
    created_at TIMESTAMP
) FROM pg_source TABLE 'public.sales_transaction';

-- Tabel Item Detail per Transaksi
CREATE TABLE sales_item (
    item_id INT PRIMARY KEY,
    transaction_id INT ,
    product_code VARCHAR,
    product_name VARCHAR,
    category VARCHAR,
    quantity INT ,
    unit_price NUMERIC ,
    discount NUMERIC ,
    total_price NUMERIC
) FROM pg_source TABLE 'public.sales_item';

-- Step 2 : Create Sink in RisingWave database to sync data from Postgres
CREATE SINK sink_sales_transaction FROM sales_transaction WITH (
    connector = 'jdbc',
    jdbc.url = 'jdbc:postgresql://postgres-slave:5432/postgres',
    user = 'postgres',
    password = 'postgres',
    table.name = 'sales_transaction',
    type = 'upsert',
    primary_key = 'transaction_id'
);

CREATE SINK sink_sales_item FROM sales_item WITH (
    connector = 'jdbc',
    jdbc.url = 'jdbc:postgresql://postgres-slave:5432/postgres',
    user = 'postgres',
    password = 'postgres',
    table.name = 'sales_item',
    type = 'upsert',
    primary_key = 'item_id'
);
