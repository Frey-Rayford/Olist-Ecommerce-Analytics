/*
Purpose: Convert staging text into typed dbo tables.
Target: SQL Server 2019
Run after 02_bulk_load_staging.sql.

This script replaces existing project data so it can be rerun safely.
*/

USE olist_analytics;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DELETE FROM dbo.order_reviews;
    DELETE FROM dbo.order_payments;
    DELETE FROM dbo.order_items;
    DELETE FROM dbo.orders;
    DELETE FROM dbo.products;
    DELETE FROM dbo.sellers;
    DELETE FROM dbo.customers;
    DELETE FROM dbo.geolocation;
    DELETE FROM dbo.category_translation;

    INSERT INTO dbo.category_translation
    (
        product_category_name,
        product_category_name_english
    )
    SELECT
        LTRIM(RTRIM(product_category_name)),
        LTRIM(RTRIM(REPLACE(product_category_name_english, CHAR(13), N'')))
    FROM stg.category_translation;

    INSERT INTO dbo.geolocation
    (
        geolocation_zip_code_prefix,
        geolocation_lat,
        geolocation_lng,
        geolocation_city,
        geolocation_state
    )
    SELECT
        RIGHT(N'00000' + LTRIM(RTRIM(geolocation_zip_code_prefix)), 5),
        TRY_CONVERT(DECIMAL(10, 7), NULLIF(geolocation_lat, N'')),
        TRY_CONVERT(DECIMAL(10, 7), NULLIF(geolocation_lng, N'')),
        LTRIM(RTRIM(geolocation_city)),
        UPPER(LTRIM(RTRIM(REPLACE(geolocation_state, CHAR(13), N''))))
    FROM stg.geolocation;

    INSERT INTO dbo.customers
    (
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    )
    SELECT
        LTRIM(RTRIM(customer_id)),
        LTRIM(RTRIM(customer_unique_id)),
        RIGHT(N'00000' + LTRIM(RTRIM(customer_zip_code_prefix)), 5),
        LTRIM(RTRIM(customer_city)),
        UPPER(LTRIM(RTRIM(REPLACE(customer_state, CHAR(13), N''))))
    FROM stg.customers;

    INSERT INTO dbo.sellers
    (
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    )
    SELECT
        LTRIM(RTRIM(seller_id)),
        RIGHT(N'00000' + LTRIM(RTRIM(seller_zip_code_prefix)), 5),
        LTRIM(RTRIM(seller_city)),
        UPPER(LTRIM(RTRIM(REPLACE(seller_state, CHAR(13), N''))))
    FROM stg.sellers;

    INSERT INTO dbo.products
    (
        product_id,
        product_category_name,
        product_name_length,
        product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,
        product_category_name_english
    )
    SELECT
        LTRIM(RTRIM(product_id)),
        NULLIF(LTRIM(RTRIM(product_category_name)), N''),
        TRY_CONVERT(INT, TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_name_length, N''))),
        TRY_CONVERT(INT, TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_description_length, N''))),
        TRY_CONVERT(INT, TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_photos_qty, N''))),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_weight_g, N'')),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_length_cm, N'')),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_height_cm, N'')),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(product_width_cm, N'')),
        NULLIF(
            LTRIM(RTRIM(REPLACE(product_category_name_english, CHAR(13), N''))),
            N''
        )
    FROM stg.products;

    INSERT INTO dbo.orders
    (
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        delivery_days,
        delivery_delay_days,
        is_late_delivery
    )
    SELECT
        LTRIM(RTRIM(order_id)),
        LTRIM(RTRIM(customer_id)),
        LTRIM(RTRIM(order_status)),
        TRY_CONVERT(DATETIME2(0), NULLIF(order_purchase_timestamp, N''), 120),
        TRY_CONVERT(DATETIME2(0), NULLIF(order_approved_at, N''), 120),
        TRY_CONVERT(DATETIME2(0), NULLIF(order_delivered_carrier_date, N''), 120),
        TRY_CONVERT(DATETIME2(0), NULLIF(order_delivered_customer_date, N''), 120),
        TRY_CONVERT(DATETIME2(0), NULLIF(order_estimated_delivery_date, N''), 120),
        TRY_CONVERT(DECIMAL(12, 6), NULLIF(delivery_days, N'')),
        TRY_CONVERT(DECIMAL(12, 6), NULLIF(delivery_delay_days, N'')),
        CASE LTRIM(RTRIM(REPLACE(is_late_delivery, CHAR(13), N'')))
            WHEN N'1' THEN CONVERT(BIT, 1)
            WHEN N'0' THEN CONVERT(BIT, 0)
            ELSE NULL
        END
    FROM stg.orders;

    INSERT INTO dbo.order_items
    (
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_date,
        price,
        freight_value,
        item_total_value
    )
    SELECT
        LTRIM(RTRIM(order_id)),
        TRY_CONVERT(INT, NULLIF(order_item_id, N'')),
        LTRIM(RTRIM(product_id)),
        LTRIM(RTRIM(seller_id)),
        TRY_CONVERT(DATETIME2(0), NULLIF(shipping_limit_date, N''), 120),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(price, N'')),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(freight_value, N'')),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(REPLACE(item_total_value, CHAR(13), N''), N''))
    FROM stg.order_items;

    INSERT INTO dbo.order_payments
    (
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    )
    SELECT
        LTRIM(RTRIM(order_id)),
        TRY_CONVERT(INT, NULLIF(payment_sequential, N'')),
        LTRIM(RTRIM(payment_type)),
        TRY_CONVERT(INT, NULLIF(payment_installments, N'')),
        TRY_CONVERT(DECIMAL(12, 2), NULLIF(REPLACE(payment_value, CHAR(13), N''), N''))
    FROM stg.order_payments;

    INSERT INTO dbo.order_reviews
    (
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp,
        has_review_comment
    )
    SELECT
        LTRIM(RTRIM(review_id)),
        LTRIM(RTRIM(order_id)),
        TRY_CONVERT(TINYINT, NULLIF(review_score, N'')),
        NULLIF(review_comment_title, N''),
        NULLIF(review_comment_message, N''),
        TRY_CONVERT(DATETIME2(0), NULLIF(review_creation_date, N''), 120),
        TRY_CONVERT(DATETIME2(0), NULLIF(review_answer_timestamp, N''), 120),
        CASE LTRIM(RTRIM(REPLACE(has_review_comment, CHAR(13), N'')))
            WHEN N'1' THEN CONVERT(BIT, 1)
            ELSE CONVERT(BIT, 0)
        END
    FROM stg.order_reviews;

    IF (SELECT COUNT_BIG(*) FROM dbo.orders) <> 99441
        THROW 50101, 'Core order row count is incorrect.', 1;
    IF (SELECT COUNT_BIG(*) FROM dbo.order_items) <> 112650
        THROW 50102, 'Core order item row count is incorrect.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;

SELECT N'customers' AS table_name, COUNT_BIG(*) AS row_count FROM dbo.customers
UNION ALL SELECT N'geolocation', COUNT_BIG(*) FROM dbo.geolocation
UNION ALL SELECT N'category_translation', COUNT_BIG(*) FROM dbo.category_translation
UNION ALL SELECT N'products', COUNT_BIG(*) FROM dbo.products
UNION ALL SELECT N'sellers', COUNT_BIG(*) FROM dbo.sellers
UNION ALL SELECT N'orders', COUNT_BIG(*) FROM dbo.orders
UNION ALL SELECT N'order_items', COUNT_BIG(*) FROM dbo.order_items
UNION ALL SELECT N'order_payments', COUNT_BIG(*) FROM dbo.order_payments
UNION ALL SELECT N'order_reviews', COUNT_BIG(*) FROM dbo.order_reviews;
GO
