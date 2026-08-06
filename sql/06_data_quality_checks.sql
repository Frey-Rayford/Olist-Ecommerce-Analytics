/*
Purpose: Validate row counts, keys, relationships and important values.
Target: SQL Server 2019
Healthy key/orphan checks should return zero.
*/

USE olist_analytics;
GO

/* 1. Expected row counts */
WITH row_counts AS
(
    SELECT N'customers' AS table_name, COUNT_BIG(*) AS actual_rows, CONVERT(BIGINT, 99441) AS expected_rows FROM dbo.customers
    UNION ALL SELECT N'geolocation', COUNT_BIG(*), 19015 FROM dbo.geolocation
    UNION ALL SELECT N'category_translation', COUNT_BIG(*), 71 FROM dbo.category_translation
    UNION ALL SELECT N'products', COUNT_BIG(*), 32951 FROM dbo.products
    UNION ALL SELECT N'sellers', COUNT_BIG(*), 3095 FROM dbo.sellers
    UNION ALL SELECT N'orders', COUNT_BIG(*), 99441 FROM dbo.orders
    UNION ALL SELECT N'order_items', COUNT_BIG(*), 112650 FROM dbo.order_items
    UNION ALL SELECT N'order_payments', COUNT_BIG(*), 103886 FROM dbo.order_payments
    UNION ALL SELECT N'order_reviews', COUNT_BIG(*), 99224 FROM dbo.order_reviews
)
SELECT
    table_name,
    actual_rows,
    expected_rows,
    CASE WHEN actual_rows = expected_rows THEN 'PASS' ELSE 'FAIL' END AS status
FROM row_counts
ORDER BY table_name;
GO

/* 2. Duplicate-key checks: every result should be zero */
SELECT N'customers.customer_id' AS check_name, COUNT_BIG(*) AS issue_count
FROM (SELECT customer_id FROM dbo.customers GROUP BY customer_id HAVING COUNT_BIG(*) > 1) AS d
UNION ALL
SELECT N'orders.order_id', COUNT_BIG(*)
FROM (SELECT order_id FROM dbo.orders GROUP BY order_id HAVING COUNT_BIG(*) > 1) AS d
UNION ALL
SELECT N'products.product_id', COUNT_BIG(*)
FROM (SELECT product_id FROM dbo.products GROUP BY product_id HAVING COUNT_BIG(*) > 1) AS d
UNION ALL
SELECT N'order_items composite key', COUNT_BIG(*)
FROM
(
    SELECT order_id, order_item_id
    FROM dbo.order_items
    GROUP BY order_id, order_item_id
    HAVING COUNT_BIG(*) > 1
) AS d;
GO

/* 3. Orphan checks: every result should be zero */
SELECT N'orders without customer' AS check_name, COUNT_BIG(*) AS issue_count
FROM dbo.orders AS o
LEFT JOIN dbo.customers AS c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT N'items without order', COUNT_BIG(*)
FROM dbo.order_items AS i
LEFT JOIN dbo.orders AS o ON o.order_id = i.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT N'items without product', COUNT_BIG(*)
FROM dbo.order_items AS i
LEFT JOIN dbo.products AS p ON p.product_id = i.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT N'items without seller', COUNT_BIG(*)
FROM dbo.order_items AS i
LEFT JOIN dbo.sellers AS s ON s.seller_id = i.seller_id
WHERE s.seller_id IS NULL
UNION ALL
SELECT N'payments without order', COUNT_BIG(*)
FROM dbo.order_payments AS p
LEFT JOIN dbo.orders AS o ON o.order_id = p.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT N'reviews without order', COUNT_BIG(*)
FROM dbo.order_reviews AS r
LEFT JOIN dbo.orders AS o ON o.order_id = r.order_id
WHERE o.order_id IS NULL;
GO

/* 4. Nulls and accepted reference gaps */
SELECT
    SUM(CASE WHEN order_approved_at IS NULL THEN 1 ELSE 0 END) AS missing_approved_at,
    SUM(CASE WHEN order_delivered_carrier_date IS NULL THEN 1 ELSE 0 END) AS missing_carrier_date,
    SUM(CASE WHEN order_delivered_customer_date IS NULL THEN 1 ELSE 0 END) AS missing_customer_delivery_date
FROM dbo.orders;

SELECT
    SUM(CASE WHEN product_category_name IS NULL THEN 1 ELSE 0 END) AS missing_category,
    SUM(CASE WHEN product_weight_g IS NULL THEN 1 ELSE 0 END) AS missing_weight,
    SUM(CASE WHEN product_length_cm IS NULL THEN 1 ELSE 0 END) AS missing_length,
    SUM(CASE WHEN product_height_cm IS NULL THEN 1 ELSE 0 END) AS missing_height,
    SUM(CASE WHEN product_width_cm IS NULL THEN 1 ELSE 0 END) AS missing_width
FROM dbo.products;
GO

/* 5. Business-rule checks */
SELECT
    SUM(CASE WHEN price < 0 THEN 1 ELSE 0 END) AS negative_prices,
    SUM(CASE WHEN freight_value < 0 THEN 1 ELSE 0 END) AS negative_freight,
    SUM(CASE WHEN ABS(item_total_value - price - freight_value) > 0.01 THEN 1 ELSE 0 END) AS incorrect_item_totals
FROM dbo.order_items;

SELECT
    SUM
    (
        CASE
            WHEN order_delivered_customer_date < order_purchase_timestamp THEN 1
            ELSE 0
        END
    ) AS delivery_before_purchase,
    SUM
    (
        CASE
            WHEN order_approved_at < order_purchase_timestamp THEN 1
            ELSE 0
        END
    ) AS approval_before_purchase
FROM dbo.orders;
GO
