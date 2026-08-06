/*
Purpose: Load the nine processed CSV files into staging tables.
Target: SQL Server 2019

Important:
- SQL Server reads the files, not VS Code.
- The SQL Server service account needs read access to @data_path.
- Change @data_path if the project folder is moved.
*/

USE olist_analytics;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @data_path NVARCHAR(4000) =
    N'<PROJECT_PATH>\data\processed';

TRUNCATE TABLE stg.order_reviews;
TRUNCATE TABLE stg.order_payments;
TRUNCATE TABLE stg.order_items;
TRUNCATE TABLE stg.orders;
TRUNCATE TABLE stg.products;
TRUNCATE TABLE stg.sellers;
TRUNCATE TABLE stg.customers;
TRUNCATE TABLE stg.geolocation;
TRUNCATE TABLE stg.category_translation;

EXEC
(
    N'BULK INSERT stg.customers FROM ''' + @data_path
    + N'\olist_customers.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.geolocation FROM ''' + @data_path
    + N'\olist_geolocation_by_zip.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.category_translation FROM ''' + @data_path
    + N'\product_category_name_translation.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.products FROM ''' + @data_path
    + N'\olist_products.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.sellers FROM ''' + @data_path
    + N'\olist_sellers.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.orders FROM ''' + @data_path
    + N'\olist_orders.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.order_items FROM ''' + @data_path
    + N'\olist_order_items.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.order_payments FROM ''' + @data_path
    + N'\olist_order_payments.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

EXEC
(
    N'BULK INSERT stg.order_reviews FROM ''' + @data_path
    + N'\olist_order_reviews.csv'' WITH
      (FORMAT = ''CSV'', FIRSTROW = 2, FIELDQUOTE = ''"'',
       ROWTERMINATOR = ''0x0a'', CODEPAGE = ''65001'', TABLOCK);'
);

IF (SELECT COUNT_BIG(*) FROM stg.customers) <> 99441
    THROW 50001, 'Unexpected row count in stg.customers.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.geolocation) <> 19015
    THROW 50002, 'Unexpected row count in stg.geolocation.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.category_translation) <> 71
    THROW 50003, 'Unexpected row count in stg.category_translation.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.products) <> 32951
    THROW 50004, 'Unexpected row count in stg.products.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.sellers) <> 3095
    THROW 50005, 'Unexpected row count in stg.sellers.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.orders) <> 99441
    THROW 50006, 'Unexpected row count in stg.orders.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.order_items) <> 112650
    THROW 50007, 'Unexpected row count in stg.order_items.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.order_payments) <> 103886
    THROW 50008, 'Unexpected row count in stg.order_payments.', 1;
IF (SELECT COUNT_BIG(*) FROM stg.order_reviews) <> 99224
    THROW 50009, 'Unexpected row count in stg.order_reviews.', 1;

SELECT N'customers' AS table_name, COUNT_BIG(*) AS row_count FROM stg.customers
UNION ALL SELECT N'geolocation', COUNT_BIG(*) FROM stg.geolocation
UNION ALL SELECT N'category_translation', COUNT_BIG(*) FROM stg.category_translation
UNION ALL SELECT N'products', COUNT_BIG(*) FROM stg.products
UNION ALL SELECT N'sellers', COUNT_BIG(*) FROM stg.sellers
UNION ALL SELECT N'orders', COUNT_BIG(*) FROM stg.orders
UNION ALL SELECT N'order_items', COUNT_BIG(*) FROM stg.order_items
UNION ALL SELECT N'order_payments', COUNT_BIG(*) FROM stg.order_payments
UNION ALL SELECT N'order_reviews', COUNT_BIG(*) FROM stg.order_reviews;
GO

