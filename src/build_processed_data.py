"""Build cleaned, analysis-ready Olist tables from immutable raw CSV files."""

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

REQUIRED_RAW_FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def validate_inputs() -> None:
    missing = [filename for filename in REQUIRED_RAW_FILES if not (RAW_DIR / filename).exists()]
    if missing:
        missing_list = "\n".join(f"- {filename}" for filename in missing)
        raise FileNotFoundError(
            "Missing required files in data/raw:\n"
            f"{missing_list}\nSee data/README.md for dataset setup instructions."
        )


def clean_text(data: pd.DataFrame) -> pd.DataFrame:
    """Trim surrounding whitespace while preserving missing values."""
    for column in data.select_dtypes(include=["object", "string"]).columns:
        data[column] = data[column].astype("string").str.strip()
    return data


def save(data: pd.DataFrame, filename: str) -> None:
    data.to_csv(PROCESSED_DIR / filename, index=False, encoding="utf-8")
    print(f"SAVED|{filename}|{len(data)}|{len(data.columns)}")


def most_frequent(values: pd.Series):
    modes = values.dropna().mode()
    return modes.iloc[0] if not modes.empty else pd.NA


def main() -> None:
    validate_inputs()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(RAW_DIR / "olist_customers_dataset.csv")
    customers = clean_text(customers)
    customers["customer_zip_code_prefix"] = (
        customers["customer_zip_code_prefix"].astype("string").str.zfill(5)
    )
    customers["customer_state"] = customers["customer_state"].str.upper()
    save(customers, "olist_customers.csv")

    geolocation = pd.read_csv(RAW_DIR / "olist_geolocation_dataset.csv")
    geolocation = clean_text(geolocation)
    geolocation["geolocation_zip_code_prefix"] = (
        geolocation["geolocation_zip_code_prefix"].astype("string").str.zfill(5)
    )
    geolocation["geolocation_state"] = geolocation["geolocation_state"].str.upper()
    geolocation_by_zip = (
        geolocation.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
            geolocation_city=("geolocation_city", most_frequent),
            geolocation_state=("geolocation_state", most_frequent),
        )
        .sort_values("geolocation_zip_code_prefix")
    )
    save(geolocation_by_zip, "olist_geolocation_by_zip.csv")

    order_items = pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv")
    order_items = clean_text(order_items)
    order_items["shipping_limit_date"] = pd.to_datetime(
        order_items["shipping_limit_date"], errors="coerce"
    )
    order_items["item_total_value"] = (
        order_items["price"] + order_items["freight_value"]
    )
    save(order_items, "olist_order_items.csv")

    payments = pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv")
    payments = clean_text(payments)
    save(payments, "olist_order_payments.csv")

    reviews = pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv")
    reviews = clean_text(reviews)
    for column in ["review_creation_date", "review_answer_timestamp"]:
        reviews[column] = pd.to_datetime(reviews[column], errors="coerce")
    reviews["has_review_comment"] = (
        reviews["review_comment_message"].notna().astype("int8")
    )
    save(reviews, "olist_order_reviews.csv")

    orders = pd.read_csv(RAW_DIR / "olist_orders_dataset.csv")
    orders = clean_text(orders)
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for column in date_columns:
        orders[column] = pd.to_datetime(orders[column], errors="coerce")
    orders["delivery_days"] = (
        orders["order_delivered_customer_date"]
        - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86_400
    orders["delivery_delay_days"] = (
        orders["order_delivered_customer_date"].dt.normalize()
        - orders["order_estimated_delivery_date"].dt.normalize()
    ).dt.total_seconds() / 86_400
    orders["is_late_delivery"] = orders["delivery_delay_days"].gt(0).astype("Int8")
    orders.loc[orders["delivery_delay_days"].isna(), "is_late_delivery"] = pd.NA
    save(orders, "olist_orders.csv")

    translation = pd.read_csv(
        RAW_DIR / "product_category_name_translation.csv"
    )
    translation = clean_text(translation)
    save(translation, "product_category_name_translation.csv")

    products = pd.read_csv(RAW_DIR / "olist_products_dataset.csv")
    products = clean_text(products)
    products = products.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )
    products = products.merge(
        translation, how="left", on="product_category_name", validate="many_to_one"
    )
    products["product_category_name_english"] = products[
        "product_category_name_english"
    ].fillna(products["product_category_name"])
    save(products, "olist_products.csv")

    sellers = pd.read_csv(RAW_DIR / "olist_sellers_dataset.csv")
    sellers = clean_text(sellers)
    sellers["seller_zip_code_prefix"] = (
        sellers["seller_zip_code_prefix"].astype("string").str.zfill(5)
    )
    sellers["seller_state"] = sellers["seller_state"].str.upper()
    save(sellers, "olist_sellers.csv")


if __name__ == "__main__":
    main()
