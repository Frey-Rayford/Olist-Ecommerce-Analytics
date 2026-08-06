/*
Purpose: Portfolio-ready exploratory KPI queries.
Target: SQL Server 2019

GMV queries use delivered orders only so cancelled or unavailable orders
are not counted as realised marketplace sales.
*/

USE olist_analytics;
GO

/* 1. Executive KPI summary */
SELECT
    COUNT_BIG(*) AS delivered_orders,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    SUM(product_value) AS product_value_brl,
    SUM(freight_value) AS freight_value_brl,
    SUM(payment_value) AS delivered_gmv_brl,
    AVG(payment_value) AS average_order_value_brl,
    AVG(delivery_days) AS average_delivery_days,
    100.0 * AVG(CONVERT(DECIMAL(10, 4), is_late_delivery)) AS late_delivery_rate_pct,
    AVG(average_review_score) AS average_review_score
FROM dbo.vw_order_summary
WHERE order_status = 'delivered';
GO

/* 2. Monthly delivered GMV, orders and month-over-month growth */
WITH monthly_sales AS
(
    SELECT
        purchase_month,
        COUNT_BIG(*) AS delivered_orders,
        SUM(payment_value) AS gmv_brl,
        AVG(payment_value) AS average_order_value_brl
    FROM dbo.vw_order_summary
    WHERE order_status = 'delivered'
    GROUP BY purchase_month
),
with_previous_month AS
(
    SELECT
        *,
        LAG(gmv_brl) OVER (ORDER BY purchase_month) AS previous_month_gmv
    FROM monthly_sales
)
SELECT
    purchase_month,
    delivered_orders,
    gmv_brl,
    average_order_value_brl,
    100.0 * (gmv_brl - previous_month_gmv)
        / NULLIF(previous_month_gmv, 0) AS gmv_growth_pct
FROM with_previous_month
ORDER BY purchase_month;
GO

/* 3. Top 10 product categories by delivered product value */
SELECT TOP (10)
    product_category,
    COUNT(DISTINCT order_id) AS orders,
    SUM(price) AS product_value_brl,
    SUM(freight_value) AS freight_value_brl,
    SUM(item_total_value) AS total_value_brl
FROM dbo.vw_order_item_detail
WHERE order_status = 'delivered'
GROUP BY product_category
ORDER BY product_value_brl DESC;
GO

/* 4. Customer states by delivered GMV */
SELECT
    customer_state,
    COUNT_BIG(*) AS delivered_orders,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    SUM(payment_value) AS gmv_brl,
    AVG(payment_value) AS average_order_value_brl
FROM dbo.vw_order_summary
WHERE order_status = 'delivered'
GROUP BY customer_state
ORDER BY gmv_brl DESC;
GO

/* 5. Delivery performance by customer state */
SELECT
    customer_state,
    COUNT_BIG(*) AS delivered_orders,
    AVG(delivery_days) AS average_delivery_days,
    AVG(delivery_delay_days) AS average_days_vs_estimate,
    100.0 * AVG(CONVERT(DECIMAL(10, 4), is_late_delivery)) AS late_delivery_rate_pct,
    AVG(average_review_score) AS average_review_score
FROM dbo.vw_order_summary
WHERE order_status = 'delivered'
GROUP BY customer_state
HAVING COUNT_BIG(*) >= 100
ORDER BY late_delivery_rate_pct DESC;
GO

/* 6. Repeat-customer rate */
WITH customer_orders AS
(
    SELECT
        customer_unique_id,
        COUNT_BIG(*) AS delivered_orders
    FROM dbo.vw_order_summary
    WHERE order_status = 'delivered'
    GROUP BY customer_unique_id
)
SELECT
    COUNT_BIG(*) AS customers,
    SUM(CASE WHEN delivered_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    100.0 * SUM(CASE WHEN delivered_orders > 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT_BIG(*), 0) AS repeat_customer_rate_pct
FROM customer_orders;
GO

/* 7. Payment method mix */
SELECT
    p.payment_type,
    COUNT_BIG(*) AS payment_records,
    COUNT(DISTINCT p.order_id) AS orders,
    SUM(p.payment_value) AS payment_value_brl,
    AVG(CONVERT(DECIMAL(10, 2), p.payment_installments)) AS average_installments
FROM dbo.order_payments AS p
INNER JOIN dbo.orders AS o
    ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.payment_type
ORDER BY payment_value_brl DESC;
GO

/* 8. Review-score distribution */
SELECT
    r.review_score,
    COUNT_BIG(*) AS reviews,
    100.0 * COUNT_BIG(*) / SUM(COUNT_BIG(*)) OVER () AS review_share_pct
FROM dbo.order_reviews AS r
INNER JOIN dbo.orders AS o
    ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY r.review_score
ORDER BY r.review_score;
GO

/* 9. Relationship between late delivery and customer satisfaction */
SELECT
    CASE
        WHEN is_late_delivery = 1 THEN 'late'
        ELSE 'on_time_or_early'
    END AS delivery_group,
    COUNT_BIG(*) AS delivered_orders,
    AVG(delivery_days) AS average_delivery_days,
    AVG(average_review_score) AS average_review_score
FROM dbo.vw_order_summary
WHERE order_status = 'delivered'
  AND is_late_delivery IS NOT NULL
GROUP BY is_late_delivery
ORDER BY is_late_delivery;
GO

/* 10. Comparable January-August year-over-year delivered GMV */
WITH comparable_period AS
(
    SELECT
        YEAR(purchase_date) AS sales_year,
        COUNT_BIG(*) AS delivered_orders,
        SUM(payment_value) AS gmv_brl
    FROM dbo.vw_order_summary
    WHERE order_status = 'delivered'
      AND YEAR(purchase_date) IN (2017, 2018)
      AND MONTH(purchase_date) BETWEEN 1 AND 8
    GROUP BY YEAR(purchase_date)
),
with_previous_year AS
(
    SELECT
        *,
        LAG(gmv_brl) OVER (ORDER BY sales_year) AS previous_year_gmv
    FROM comparable_period
)
SELECT
    sales_year,
    delivered_orders,
    gmv_brl,
    100.0 * (gmv_brl - previous_year_gmv)
        / NULLIF(previous_year_gmv, 0) AS gmv_growth_pct
FROM with_previous_year
ORDER BY sales_year;
GO
