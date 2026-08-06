/*
Purpose: Create reusable analysis views.
Target: SQL Server 2019
Run after 03_transform_to_core.sql.
*/

USE olist_analytics;
GO

CREATE OR ALTER VIEW dbo.vw_order_summary
AS
WITH item_metrics AS
(
    SELECT
        order_id,
        COUNT(*) AS item_count,
        COUNT(DISTINCT product_id) AS product_count,
        COUNT(DISTINCT seller_id) AS seller_count,
        SUM(price) AS product_value,
        SUM(freight_value) AS freight_value,
        SUM(item_total_value) AS order_value
    FROM dbo.order_items
    GROUP BY order_id
),
payment_metrics AS
(
    SELECT
        order_id,
        COUNT(*) AS payment_record_count,
        COUNT(DISTINCT payment_type) AS payment_type_count,
        MAX(payment_installments) AS max_installments,
        SUM(payment_value) AS payment_value
    FROM dbo.order_payments
    GROUP BY order_id
),
review_metrics AS
(
    SELECT
        order_id,
        COUNT(*) AS review_count,
        AVG(CONVERT(DECIMAL(10, 4), review_score)) AS average_review_score,
        MAX(CONVERT(TINYINT, has_review_comment)) AS has_review_comment
    FROM dbo.order_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    CONVERT(DATE, o.order_purchase_timestamp) AS purchase_date,
    DATEFROMPARTS
    (
        YEAR(o.order_purchase_timestamp),
        MONTH(o.order_purchase_timestamp),
        1
    ) AS purchase_month,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    o.delivery_days,
    o.delivery_delay_days,
    o.is_late_delivery,
    COALESCE(i.item_count, 0) AS item_count,
    COALESCE(i.product_count, 0) AS product_count,
    COALESCE(i.seller_count, 0) AS seller_count,
    COALESCE(i.product_value, 0) AS product_value,
    COALESCE(i.freight_value, 0) AS freight_value,
    COALESCE(i.order_value, 0) AS order_value,
    COALESCE(p.payment_record_count, 0) AS payment_record_count,
    COALESCE(p.payment_type_count, 0) AS payment_type_count,
    COALESCE(p.max_installments, 0) AS max_installments,
    COALESCE(p.payment_value, 0) AS payment_value,
    COALESCE(p.payment_value, 0) - COALESCE(i.order_value, 0) AS payment_difference,
    COALESCE(r.review_count, 0) AS review_count,
    r.average_review_score,
    COALESCE(r.has_review_comment, 0) AS has_review_comment
FROM dbo.orders AS o
INNER JOIN dbo.customers AS c
    ON c.customer_id = o.customer_id
LEFT JOIN item_metrics AS i
    ON i.order_id = o.order_id
LEFT JOIN payment_metrics AS p
    ON p.order_id = o.order_id
LEFT JOIN review_metrics AS r
    ON r.order_id = o.order_id;
GO

CREATE OR ALTER VIEW dbo.vw_order_item_detail
AS
SELECT
    oi.order_id,
    oi.order_item_id,
    o.order_status,
    o.order_purchase_timestamp,
    CONVERT(DATE, o.order_purchase_timestamp) AS purchase_date,
    DATEFROMPARTS
    (
        YEAR(o.order_purchase_timestamp),
        MONTH(o.order_purchase_timestamp),
        1
    ) AS purchase_month,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    oi.product_id,
    COALESCE(p.product_category_name_english, N'unknown') AS product_category,
    oi.seller_id,
    s.seller_city,
    s.seller_state,
    oi.price,
    oi.freight_value,
    oi.item_total_value,
    o.delivery_days,
    o.delivery_delay_days,
    o.is_late_delivery
FROM dbo.order_items AS oi
INNER JOIN dbo.orders AS o
    ON o.order_id = oi.order_id
INNER JOIN dbo.customers AS c
    ON c.customer_id = o.customer_id
INNER JOIN dbo.products AS p
    ON p.product_id = oi.product_id
INNER JOIN dbo.sellers AS s
    ON s.seller_id = oi.seller_id;
GO

