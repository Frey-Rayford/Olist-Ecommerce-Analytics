/*
Purpose: Create text-based staging tables and typed analytics tables.
Target: SQL Server 2019
Run after 00_create_database.sql.
*/

USE olist_analytics;
GO

SET NOCOUNT ON;
GO

/* Staging tables keep CSV values as text for safe loading. */

IF OBJECT_ID(N'stg.customers', N'U') IS NULL
BEGIN
    CREATE TABLE stg.customers
    (
        customer_id NVARCHAR(100) NULL,
        customer_unique_id NVARCHAR(100) NULL,
        customer_zip_code_prefix NVARCHAR(20) NULL,
        customer_city NVARCHAR(200) NULL,
        customer_state NVARCHAR(20) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.geolocation', N'U') IS NULL
BEGIN
    CREATE TABLE stg.geolocation
    (
        geolocation_zip_code_prefix NVARCHAR(20) NULL,
        geolocation_lat NVARCHAR(50) NULL,
        geolocation_lng NVARCHAR(50) NULL,
        geolocation_city NVARCHAR(200) NULL,
        geolocation_state NVARCHAR(20) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.category_translation', N'U') IS NULL
BEGIN
    CREATE TABLE stg.category_translation
    (
        product_category_name NVARCHAR(200) NULL,
        product_category_name_english NVARCHAR(200) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.products', N'U') IS NULL
BEGIN
    CREATE TABLE stg.products
    (
        product_id NVARCHAR(100) NULL,
        product_category_name NVARCHAR(200) NULL,
        product_name_length NVARCHAR(50) NULL,
        product_description_length NVARCHAR(50) NULL,
        product_photos_qty NVARCHAR(50) NULL,
        product_weight_g NVARCHAR(50) NULL,
        product_length_cm NVARCHAR(50) NULL,
        product_height_cm NVARCHAR(50) NULL,
        product_width_cm NVARCHAR(50) NULL,
        product_category_name_english NVARCHAR(200) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.sellers', N'U') IS NULL
BEGIN
    CREATE TABLE stg.sellers
    (
        seller_id NVARCHAR(100) NULL,
        seller_zip_code_prefix NVARCHAR(20) NULL,
        seller_city NVARCHAR(200) NULL,
        seller_state NVARCHAR(20) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.orders', N'U') IS NULL
BEGIN
    CREATE TABLE stg.orders
    (
        order_id NVARCHAR(100) NULL,
        customer_id NVARCHAR(100) NULL,
        order_status NVARCHAR(50) NULL,
        order_purchase_timestamp NVARCHAR(50) NULL,
        order_approved_at NVARCHAR(50) NULL,
        order_delivered_carrier_date NVARCHAR(50) NULL,
        order_delivered_customer_date NVARCHAR(50) NULL,
        order_estimated_delivery_date NVARCHAR(50) NULL,
        delivery_days NVARCHAR(50) NULL,
        delivery_delay_days NVARCHAR(50) NULL,
        is_late_delivery NVARCHAR(20) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.order_items', N'U') IS NULL
BEGIN
    CREATE TABLE stg.order_items
    (
        order_id NVARCHAR(100) NULL,
        order_item_id NVARCHAR(50) NULL,
        product_id NVARCHAR(100) NULL,
        seller_id NVARCHAR(100) NULL,
        shipping_limit_date NVARCHAR(50) NULL,
        price NVARCHAR(50) NULL,
        freight_value NVARCHAR(50) NULL,
        item_total_value NVARCHAR(50) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.order_payments', N'U') IS NULL
BEGIN
    CREATE TABLE stg.order_payments
    (
        order_id NVARCHAR(100) NULL,
        payment_sequential NVARCHAR(50) NULL,
        payment_type NVARCHAR(100) NULL,
        payment_installments NVARCHAR(50) NULL,
        payment_value NVARCHAR(50) NULL
    );
END;
GO

IF OBJECT_ID(N'stg.order_reviews', N'U') IS NULL
BEGIN
    CREATE TABLE stg.order_reviews
    (
        review_id NVARCHAR(100) NULL,
        order_id NVARCHAR(100) NULL,
        review_score NVARCHAR(50) NULL,
        review_comment_title NVARCHAR(MAX) NULL,
        review_comment_message NVARCHAR(MAX) NULL,
        review_creation_date NVARCHAR(50) NULL,
        review_answer_timestamp NVARCHAR(50) NULL,
        has_review_comment NVARCHAR(20) NULL
    );
END;
GO

/* Typed core tables used by analysis queries. */

IF OBJECT_ID(N'dbo.customers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customers
    (
        customer_id CHAR(32) NOT NULL CONSTRAINT PK_customers PRIMARY KEY,
        customer_unique_id CHAR(32) NOT NULL,
        customer_zip_code_prefix CHAR(5) NOT NULL,
        customer_city NVARCHAR(100) NOT NULL,
        customer_state CHAR(2) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.geolocation', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.geolocation
    (
        geolocation_zip_code_prefix CHAR(5) NOT NULL CONSTRAINT PK_geolocation PRIMARY KEY,
        geolocation_lat DECIMAL(10, 7) NOT NULL,
        geolocation_lng DECIMAL(10, 7) NOT NULL,
        geolocation_city NVARCHAR(100) NOT NULL,
        geolocation_state CHAR(2) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.category_translation', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.category_translation
    (
        product_category_name NVARCHAR(100) NOT NULL CONSTRAINT PK_category_translation PRIMARY KEY,
        product_category_name_english NVARCHAR(100) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.products', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.products
    (
        product_id CHAR(32) NOT NULL CONSTRAINT PK_products PRIMARY KEY,
        product_category_name NVARCHAR(100) NULL,
        product_name_length INT NULL,
        product_description_length INT NULL,
        product_photos_qty INT NULL,
        product_weight_g DECIMAL(12, 2) NULL,
        product_length_cm DECIMAL(12, 2) NULL,
        product_height_cm DECIMAL(12, 2) NULL,
        product_width_cm DECIMAL(12, 2) NULL,
        product_category_name_english NVARCHAR(100) NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.sellers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sellers
    (
        seller_id CHAR(32) NOT NULL CONSTRAINT PK_sellers PRIMARY KEY,
        seller_zip_code_prefix CHAR(5) NOT NULL,
        seller_city NVARCHAR(100) NOT NULL,
        seller_state CHAR(2) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.orders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.orders
    (
        order_id CHAR(32) NOT NULL CONSTRAINT PK_orders PRIMARY KEY,
        customer_id CHAR(32) NOT NULL,
        order_status VARCHAR(30) NOT NULL,
        order_purchase_timestamp DATETIME2(0) NOT NULL,
        order_approved_at DATETIME2(0) NULL,
        order_delivered_carrier_date DATETIME2(0) NULL,
        order_delivered_customer_date DATETIME2(0) NULL,
        order_estimated_delivery_date DATETIME2(0) NOT NULL,
        delivery_days DECIMAL(12, 6) NULL,
        delivery_delay_days DECIMAL(12, 6) NULL,
        is_late_delivery BIT NULL,
        CONSTRAINT FK_orders_customers
            FOREIGN KEY (customer_id) REFERENCES dbo.customers(customer_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.order_items', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_items
    (
        order_id CHAR(32) NOT NULL,
        order_item_id INT NOT NULL,
        product_id CHAR(32) NOT NULL,
        seller_id CHAR(32) NOT NULL,
        shipping_limit_date DATETIME2(0) NOT NULL,
        price DECIMAL(12, 2) NOT NULL,
        freight_value DECIMAL(12, 2) NOT NULL,
        item_total_value DECIMAL(12, 2) NOT NULL,
        CONSTRAINT PK_order_items PRIMARY KEY (order_id, order_item_id),
        CONSTRAINT FK_order_items_orders
            FOREIGN KEY (order_id) REFERENCES dbo.orders(order_id),
        CONSTRAINT FK_order_items_products
            FOREIGN KEY (product_id) REFERENCES dbo.products(product_id),
        CONSTRAINT FK_order_items_sellers
            FOREIGN KEY (seller_id) REFERENCES dbo.sellers(seller_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.order_payments', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_payments
    (
        order_id CHAR(32) NOT NULL,
        payment_sequential INT NOT NULL,
        payment_type VARCHAR(50) NOT NULL,
        payment_installments INT NOT NULL,
        payment_value DECIMAL(12, 2) NOT NULL,
        CONSTRAINT PK_order_payments PRIMARY KEY (order_id, payment_sequential),
        CONSTRAINT FK_order_payments_orders
            FOREIGN KEY (order_id) REFERENCES dbo.orders(order_id)
    );
END;
GO

IF OBJECT_ID(N'dbo.order_reviews', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_reviews
    (
        review_id CHAR(32) NOT NULL,
        order_id CHAR(32) NOT NULL,
        review_score TINYINT NOT NULL,
        review_comment_title NVARCHAR(MAX) NULL,
        review_comment_message NVARCHAR(MAX) NULL,
        review_creation_date DATETIME2(0) NOT NULL,
        review_answer_timestamp DATETIME2(0) NOT NULL,
        has_review_comment BIT NOT NULL,
        CONSTRAINT PK_order_reviews PRIMARY KEY (review_id, order_id),
        CONSTRAINT FK_order_reviews_orders
            FOREIGN KEY (order_id) REFERENCES dbo.orders(order_id),
        CONSTRAINT CK_order_reviews_score CHECK (review_score BETWEEN 1 AND 5)
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customers_unique_id' AND object_id = OBJECT_ID(N'dbo.customers')
)
    CREATE INDEX IX_customers_unique_id ON dbo.customers(customer_unique_id);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_orders_purchase_date' AND object_id = OBJECT_ID(N'dbo.orders')
)
    CREATE INDEX IX_orders_purchase_date ON dbo.orders(order_purchase_timestamp);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_order_items_product' AND object_id = OBJECT_ID(N'dbo.order_items')
)
    CREATE INDEX IX_order_items_product ON dbo.order_items(product_id);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_order_items_seller' AND object_id = OBJECT_ID(N'dbo.order_items')
)
    CREATE INDEX IX_order_items_seller ON dbo.order_items(seller_id);
GO
