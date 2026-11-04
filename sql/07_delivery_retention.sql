/* Order-grain snapshot; requires the core model and vw_order_summary. */
USE olist_analytics;
GO
DECLARE @AsOfDate DATE = '2018-08-31';
DECLARE @End DATETIME2 = DATEADD(DAY, 1, CONVERT(DATETIME2, @AsOfDate));

WITH category_value AS (
    SELECT i.order_id, COALESCE(p.product_category_name_english, 'unknown') AS category,
           SUM(i.price) AS product_value
    FROM dbo.order_items i
    LEFT JOIN dbo.products p ON p.product_id = i.product_id
    GROUP BY i.order_id, COALESCE(p.product_category_name_english, 'unknown')
), ranked_category AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY product_value DESC, category) AS rank_in_order
    FROM category_value
), review_snapshot AS (
    SELECT order_id, AVG(CONVERT(FLOAT, review_score)) AS review_score
    FROM dbo.order_reviews
    WHERE review_answer_timestamp < @End AND review_score BETWEEN 1 AND 5
    GROUP BY order_id
)
SELECT o.order_id, o.customer_unique_id, o.customer_state, o.order_purchase_timestamp,
       COALESCE(c.category, 'unknown') AS primary_category, o.payment_value AS gmv,
       r.review_score,
       CASE WHEN o.order_estimated_delivery_date IS NULL THEN 'unknown'
            WHEN CONVERT(DATE, o.order_delivered_customer_date) > CONVERT(DATE, o.order_estimated_delivery_date) THEN 'late'
            ELSE 'on_time' END AS delivery_status
INTO #delivery
FROM dbo.vw_order_summary o
LEFT JOIN ranked_category c ON c.order_id = o.order_id AND c.rank_in_order = 1
LEFT JOIN review_snapshot r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered' AND o.order_purchase_timestamp < @End
  AND o.order_delivered_customer_date < @End;

SELECT customer_state, COUNT(*) AS delivered_orders,
       SUM(CASE WHEN delivery_status = 'late' THEN 1 ELSE 0 END) AS late_orders,
       1.0 * SUM(CASE WHEN delivery_status = 'late' THEN 1 ELSE 0 END)
         / NULLIF(SUM(CASE WHEN delivery_status <> 'unknown' THEN 1 ELSE 0 END), 0) AS late_rate,
       COUNT(review_score) AS reviewed_orders,
       AVG(CASE WHEN delivery_status = 'late' THEN review_score END) AS late_review,
       AVG(CASE WHEN delivery_status = 'on_time' THEN review_score END) AS on_time_review
FROM #delivery GROUP BY customer_state ORDER BY late_orders DESC;

WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp, order_id) AS purchase_rank
    FROM #delivery
), first_order AS (
    SELECT * FROM ranked WHERE purchase_rank = 1
), eligible AS (
    SELECT f.*, CASE WHEN EXISTS (
        SELECT 1 FROM #delivery n
        WHERE n.customer_unique_id = f.customer_unique_id
          AND n.order_purchase_timestamp > f.order_purchase_timestamp
          AND n.order_purchase_timestamp <= DATEADD(DAY, 90, f.order_purchase_timestamp)
    ) THEN 1 ELSE 0 END AS repeats_90d
    FROM first_order f
    WHERE DATEADD(DAY, 90, f.order_purchase_timestamp) < @End
)
SELECT delivery_status AS first_delivery_status, COUNT(*) AS eligible_customers,
       SUM(repeats_90d) AS repeat_customers, 1.0 * SUM(repeats_90d) / NULLIF(COUNT(*), 0) AS repeat_rate_90d
FROM eligible GROUP BY delivery_status;

DROP TABLE #delivery;
