-- ============================================
-- Database Setup for Query Assistant
-- ============================================

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create query_history table
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    result_rows INTEGER,
    execution_time_ms FLOAT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create saved_queries table
CREATE TABLE IF NOT EXISTS saved_queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    question TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Create scheduled_reports table
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    saved_query_id INTEGER REFERENCES saved_queries(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    schedule_cron VARCHAR(100) NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'csv',
    recipients TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create role_permissions table
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    schema_name VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    can_select BOOLEAN DEFAULT FALSE,
    can_insert BOOLEAN DEFAULT FALSE,
    can_update BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    row_filter TEXT,
    column_filter TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, schema_name, table_name)
);

-- Create database_connections table
CREATE TABLE IF NOT EXISTS database_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    connection_string TEXT NOT NULL,
    database_type VARCHAR(50) NOT NULL DEFAULT 'postgresql',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Sample Data Tables (for testing)
-- ============================================

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Insert Sample Data
-- ============================================

-- Insert test user (admin)
INSERT INTO users (username, email, hashed_password, role) VALUES
    ('admin', 'admin@example.com', 'dummy_hash_replace_later', 'admin'),
    ('analyst', 'analyst@example.com', 'dummy_hash_replace_later', 'analyst'),
    ('viewer', 'viewer@example.com', 'dummy_hash_replace_later', 'viewer')
ON CONFLICT (username) DO NOTHING;

-- Insert sample customers
INSERT INTO customers (name, email, phone) VALUES
    ('John Doe', 'john@example.com', '555-0101'),
    ('Jane Smith', 'jane@example.com', '555-0102'),
    ('Bob Johnson', 'bob@example.com', '555-0103'),
    ('Alice Williams', 'alice@example.com', '555-0104'),
    ('Charlie Brown', 'charlie@example.com', '555-0105')
ON CONFLICT (email) DO NOTHING;

-- Insert sample products
INSERT INTO products (name, description, price, stock_quantity, category) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 50, 'Electronics'),
    ('Mouse', 'Wireless mouse', 29.99, 200, 'Electronics'),
    ('Keyboard', 'Mechanical keyboard', 89.99, 150, 'Electronics'),
    ('Monitor', '27-inch 4K monitor', 449.99, 75, 'Electronics'),
    ('Desk Chair', 'Ergonomic office chair', 299.99, 30, 'Furniture'),
    ('Desk Lamp', 'LED desk lamp', 39.99, 100, 'Furniture'),
    ('Notebook', 'A4 ruled notebook', 5.99, 500, 'Stationery'),
    ('Pen Set', 'Professional pen set', 19.99, 300, 'Stationery')
ON CONFLICT DO NOTHING;

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, amount, status) VALUES
    (1, CURRENT_TIMESTAMP - INTERVAL '30 days', 1329.98, 'completed'),
    (1, CURRENT_TIMESTAMP - INTERVAL '25 days', 89.99, 'completed'),
    (2, CURRENT_TIMESTAMP - INTERVAL '20 days', 449.99, 'completed'),
    (2, CURRENT_TIMESTAMP - INTERVAL '15 days', 299.99, 'completed'),
    (3, CURRENT_TIMESTAMP - INTERVAL '10 days', 69.97, 'completed'),
    (3, CURRENT_TIMESTAMP - INTERVAL '5 days', 1299.99, 'pending'),
    (4, CURRENT_TIMESTAMP - INTERVAL '3 days', 39.99, 'completed'),
    (5, CURRENT_TIMESTAMP - INTERVAL '1 day', 109.98, 'pending')
ON CONFLICT DO NOTHING;

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1299.99),  -- Order 1: Laptop
    (1, 2, 1, 29.99),     -- Order 1: Mouse
    (2, 3, 1, 89.99),     -- Order 2: Keyboard
    (3, 4, 1, 449.99),    -- Order 3: Monitor
    (4, 5, 1, 299.99),    -- Order 4: Desk Chair
    (5, 2, 1, 29.99),     -- Order 5: Mouse
    (5, 6, 1, 39.99),     -- Order 5: Desk Lamp
    (6, 1, 1, 1299.99),   -- Order 6: Laptop
    (7, 6, 1, 39.99),     -- Order 7: Desk Lamp
    (8, 7, 10, 5.99),     -- Order 8: Notebooks
    (8, 8, 2, 19.99)      -- Order 8: Pen Sets
ON CONFLICT DO NOTHING;

-- Grant admin user full permissions
INSERT INTO role_permissions (user_id, schema_name, table_name, can_select, can_insert, can_update, can_delete)
SELECT 
    u.id,
    'public',
    t.table_name,
    TRUE,
    TRUE,
    TRUE,
    TRUE
FROM users u
CROSS JOIN information_schema.tables t
WHERE u.username = 'admin'
    AND t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
ON CONFLICT (user_id, schema_name, table_name) DO NOTHING;

-- Grant analyst user read permissions
INSERT INTO role_permissions (user_id, schema_name, table_name, can_select)
SELECT 
    u.id,
    'public',
    t.table_name,
    TRUE
FROM users u
CROSS JOIN information_schema.tables t
WHERE u.username = 'analyst'
    AND t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
ON CONFLICT (user_id, schema_name, table_name) DO NOTHING;

-- Grant viewer limited read permissions
INSERT INTO role_permissions (user_id, schema_name, table_name, can_select)
SELECT 
    u.id,
    'public',
    t.table_name,
    TRUE
FROM users u
CROSS JOIN information_schema.tables t
WHERE u.username = 'viewer'
    AND t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    AND t.table_name IN ('customers', 'orders', 'products', 'order_items')
ON CONFLICT (user_id, schema_name, table_name) DO NOTHING;

-- ============================================
-- Create Indexes for Performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at);
CREATE INDEX IF NOT EXISTS idx_saved_queries_user_id ON saved_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- ============================================
-- Success Message
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Database setup complete!';
    RAISE NOTICE '✅ Created 11 tables';
    RAISE NOTICE '✅ Inserted 3 test users (admin, analyst, viewer)';
    RAISE NOTICE '✅ Inserted sample data (5 customers, 8 products, 8 orders)';
    RAISE NOTICE '✅ Configured RBAC permissions';
    RAISE NOTICE '';
    RAISE NOTICE '📝 Test Users:';
    RAISE NOTICE '   - admin@example.com (full access)';
    RAISE NOTICE '   - analyst@example.com (read-only all tables)';
    RAISE NOTICE '   - viewer@example.com (read-only limited tables)';
END $$;