"""Run integrity checks on generated Olist processed tables."""

from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


EXPECTED_ROWS = {
    "olist_customers.csv": 99_441,
    "olist_geolocation_by_zip.csv": 19_015,
    "olist_order_items.csv": 112_650,
    "olist_order_payments.csv": 103_886,
    "olist_order_reviews.csv": 99_224,
    "olist_orders.csv": 99_441,
    "olist_products.csv": 32_951,
    "olist_sellers.csv": 3_095,
    "product_category_name_translation.csv": 71,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    tables = {
        filename: pd.read_csv(PROCESSED_DIR / filename, low_memory=False)
        for filename in EXPECTED_ROWS
    }

    for filename, expected_rows in EXPECTED_ROWS.items():
        require(len(tables[filename]) == expected_rows, f"Unexpected rows: {filename}")

    customers = tables["olist_customers.csv"]
    geolocation = tables["olist_geolocation_by_zip.csv"]
    items = tables["olist_order_items.csv"]
    payments = tables["olist_order_payments.csv"]
    reviews = tables["olist_order_reviews.csv"]
    orders = tables["olist_orders.csv"]
    products = tables["olist_products.csv"]
    sellers = tables["olist_sellers.csv"]
    customer_zip_values = pd.read_csv(
        PROCESSED_DIR / "olist_customers.csv",
        usecols=["customer_zip_code_prefix"],
        dtype={"customer_zip_code_prefix": "string"},
    )["customer_zip_code_prefix"]
    seller_zip_values = pd.read_csv(
        PROCESSED_DIR / "olist_sellers.csv",
        usecols=["seller_zip_code_prefix"],
        dtype={"seller_zip_code_prefix": "string"},
    )["seller_zip_code_prefix"]

    require(customers["customer_id"].is_unique, "customer_id is not unique")
    require(orders["order_id"].is_unique, "order_id is not unique")
    require(products["product_id"].is_unique, "product_id is not unique")
    require(sellers["seller_id"].is_unique, "seller_id is not unique")
    require(
        geolocation["geolocation_zip_code_prefix"].astype("string").is_unique,
        "geolocation zip is not unique",
    )
    require(
        not items.duplicated(["order_id", "order_item_id"]).any(),
        "order item composite key is not unique",
    )
    require(
        not payments.duplicated(["order_id", "payment_sequential"]).any(),
        "payment composite key is not unique",
    )
    require(
        not reviews.duplicated(["review_id", "order_id"]).any(),
        "review composite key is not unique",
    )

    require(
        items["order_id"].isin(orders["order_id"]).all(),
        "order_items contains unknown order_id",
    )
    require(
        payments["order_id"].isin(orders["order_id"]).all(),
        "payments contains unknown order_id",
    )
    require(
        reviews["order_id"].isin(orders["order_id"]).all(),
        "reviews contains unknown order_id",
    )
    require(
        items["product_id"].isin(products["product_id"]).all(),
        "order_items contains unknown product_id",
    )
    require(
        items["seller_id"].isin(sellers["seller_id"]).all(),
        "order_items contains unknown seller_id",
    )

    expected_item_total = items["price"] + items["freight_value"]
    require(
        (items["item_total_value"] - expected_item_total).abs().max() < 1e-8,
        "item_total_value calculation is incorrect",
    )
    require(
        "product_name_length" in products.columns
        and "product_description_length" in products.columns,
        "corrected product column names are missing",
    )
    require(
        customer_zip_values.str.len().eq(5).all(),
        "customer zip codes are not five characters",
    )
    require(
        seller_zip_values.str.len().eq(5).all(),
        "seller zip codes are not five characters",
    )
    require(
        set(reviews["has_review_comment"].dropna().unique()).issubset({0, 1}),
        "review Boolean values are not SQL-compatible 0/1",
    )
    require(
        set(orders["is_late_delivery"].dropna().unique()).issubset({0, 1}),
        "order Boolean values are not SQL-compatible 0/1",
    )

    print(f"CHECKS_OK|files={len(tables)}|orders={len(orders)}|items={len(items)}")


if __name__ == "__main__":
    main()
