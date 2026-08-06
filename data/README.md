# Dataset setup

Download the **Brazilian E-Commerce Public Dataset by Olist** from:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Place these files in `data/raw/` without renaming them:

```text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

Then run:

```powershell
python src/run_pipeline.py
```

`data/raw/` and `data/processed/` are excluded from Git because the source and generated CSV files are large. The generated `dashboard/data/analytics.json` is intentionally version-controlled so the dashboard can run after cloning the repository.
