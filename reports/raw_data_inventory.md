# Raw data inventory

Last validated: 2026-08-06

Scope: nine source CSV files in `data/raw/`. Inspection is read-only.

## File overview

| File | Rows | Columns |
|---|---:|---:|
| `olist_customers_dataset.csv` | 99,441 | 5 |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 |
| `olist_order_items_dataset.csv` | 112,650 | 7 |
| `olist_order_payments_dataset.csv` | 103,886 | 5 |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 |
| `olist_orders_dataset.csv` | 99,441 | 8 |
| `olist_products_dataset.csv` | 32,951 | 9 |
| `olist_sellers_dataset.csv` | 3,095 | 4 |
| `product_category_name_translation.csv` | 71 | 2 |
| **Total** | **1,550,922** |  |

## Important source issues

- Date and timestamp columns are stored as strings and require parsing.
- `product_name_lenght` and `product_description_lenght` are misspelled in the source dataset. Raw column names are not modified.
- Review title and comment fields are frequently missing because written feedback is optional.
- Geolocation contains many rows per ZIP prefix and must be aggregated before joining at ZIP grain.
- Product dimensions contain two missing rows in several fields.

## Missing values requiring explicit handling

| Table | Column | Missing values |
|---|---|---:|
| Reviews | `review_comment_title` | 87,656 |
| Reviews | `review_comment_message` | 58,247 |
| Orders | `order_approved_at` | 160 |
| Orders | `order_delivered_carrier_date` | 1,783 |
| Orders | `order_delivered_customer_date` | 2,965 |
| Products | `product_category_name` | 610 |
| Products | `product_name_lenght` | 610 |
| Products | `product_description_lenght` | 610 |
| Products | `product_photos_qty` | 610 |
| Products | `product_weight_g` | 2 |
| Products | `product_length_cm` | 2 |
| Products | `product_height_cm` | 2 |
| Products | `product_width_cm` | 2 |
