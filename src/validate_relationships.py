"""Validate primary-key candidates and relationships in the raw Olist data."""

from pathlib import Path

import pandas as pd


RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translation": "product_category_name_translation.csv",
}


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_csv(RAW_DIR / filename, low_memory=False)
        for name, filename in FILES.items()
    }


def check_key(table_name: str, data: pd.DataFrame, columns: list[str]) -> None:
    duplicate_rows = int(data.duplicated(columns, keep=False).sum())
    null_rows = int(data[columns].isna().any(axis=1).sum())
    print(
        "KEY|"
        f"{table_name}|{'+'.join(columns)}|{len(data)}|"
        f"{duplicate_rows}|{null_rows}"
    )


def check_fk(
    child_name: str,
    child: pd.DataFrame,
    child_column: str,
    parent_name: str,
    parent: pd.DataFrame,
    parent_column: str,
) -> None:
    child_values = child[child_column].dropna()
    parent_values = set(parent[parent_column].dropna())
    orphan_mask = ~child_values.isin(parent_values)
    print(
        "FK|"
        f"{child_name}.{child_column}|{parent_name}.{parent_column}|"
        f"{int(orphan_mask.sum())}|{int(child_values[orphan_mask].nunique())}"
    )


def main() -> None:
    tables = load_tables()

    key_candidates = [
        ("customers", ["customer_id"]),
        ("orders", ["order_id"]),
        ("products", ["product_id"]),
        ("sellers", ["seller_id"]),
        ("translation", ["product_category_name"]),
        ("order_items", ["order_id", "order_item_id"]),
        ("payments", ["order_id", "payment_sequential"]),
        ("reviews", ["review_id"]),
        ("reviews", ["review_id", "order_id"]),
        ("geolocation", ["geolocation_zip_code_prefix"]),
    ]

    for table_name, columns in key_candidates:
        check_key(table_name, tables[table_name], columns)

    relationships = [
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("order_items", "seller_id", "sellers", "seller_id"),
        ("payments", "order_id", "orders", "order_id"),
        ("reviews", "order_id", "orders", "order_id"),
        (
            "products",
            "product_category_name",
            "translation",
            "product_category_name",
        ),
        (
            "customers",
            "customer_zip_code_prefix",
            "geolocation",
            "geolocation_zip_code_prefix",
        ),
        (
            "sellers",
            "seller_zip_code_prefix",
            "geolocation",
            "geolocation_zip_code_prefix",
        ),
    ]

    for child_name, child_column, parent_name, parent_column in relationships:
        check_fk(
            child_name,
            tables[child_name],
            child_column,
            parent_name,
            tables[parent_name],
            parent_column,
        )


if __name__ == "__main__":
    main()
