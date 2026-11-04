"""Export analysis-ready JSON consumed by the Next.js dashboard.

The script reads only the processed CSV files. It aggregates every metric at the
correct grain before joining tables, which prevents payment, item, and review
rows from multiplying each other.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
DASHBOARD_DATA_DIR = PROJECT_DIR / "dashboard" / "data"
OUTPUT_FILE = DASHBOARD_DATA_DIR / "analytics.json"


def _round(value: float | int, digits: int = 2) -> float:
    return round(float(value), digits)


def _load_order_summary() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    orders = pd.read_csv(
        PROCESSED_DIR / "olist_orders.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        low_memory=False,
    )
    customers = pd.read_csv(PROCESSED_DIR / "olist_customers.csv", low_memory=False)
    items = pd.read_csv(PROCESSED_DIR / "olist_order_items.csv", low_memory=False)
    payments = pd.read_csv(PROCESSED_DIR / "olist_order_payments.csv", low_memory=False)
    reviews = pd.read_csv(PROCESSED_DIR / "olist_order_reviews.csv", low_memory=False)
    products = pd.read_csv(PROCESSED_DIR / "olist_products.csv", low_memory=False)

    item_metrics = items.groupby("order_id", as_index=False).agg(
        product_value=("price", "sum"),
        freight_value=("freight_value", "sum"),
        item_total_value=("item_total_value", "sum"),
        item_count=("order_item_id", "count"),
    )
    payment_metrics = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum")
    )
    review_metrics = reviews.groupby("order_id", as_index=False).agg(
        average_review_score=("review_score", "mean"),
        review_count=("review_id", "count"),
    )

    summary = (
        orders.merge(
            customers[["customer_id", "customer_unique_id", "customer_state"]],
            on="customer_id",
            how="left",
            validate="one_to_one",
        )
        .merge(item_metrics, on="order_id", how="left", validate="one_to_one")
        .merge(payment_metrics, on="order_id", how="left", validate="one_to_one")
        .merge(review_metrics, on="order_id", how="left", validate="one_to_one")
    )

    return summary, {
        "orders": orders,
        "customers": customers,
        "items": items,
        "payments": payments,
        "reviews": reviews,
        "products": products,
    }


def build_payload() -> dict[str, object]:
    order_summary, tables = _load_order_summary()
    delivered = order_summary.loc[
        order_summary["order_status"].eq("delivered")
    ].copy()

    delivered["purchase_month"] = (
        delivered["order_purchase_timestamp"].dt.to_period("M").astype(str)
    )

    monthly = (
        delivered.loc[
            delivered["purchase_month"].between("2017-01", "2018-08")
        ]
        .groupby("purchase_month", as_index=False)
        .agg(gmv=("payment_value", "sum"), orders=("order_id", "count"))
    )

    delivered_ids = set(delivered["order_id"])
    delivered_items = tables["items"].loc[
        tables["items"]["order_id"].isin(delivered_ids)
    ].merge(
        tables["products"][["product_id", "product_category_name_english"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    categories = (
        delivered_items.assign(
            category=lambda data: data["product_category_name_english"].fillna(
                "unknown"
            )
        )
        .groupby("category", as_index=False)
        .agg(product_value=("price", "sum"), orders=("order_id", "nunique"))
        .sort_values("product_value", ascending=False)
        .head(5)
    )

    states = (
        delivered.groupby("customer_state", as_index=False)
        .agg(
            gmv=("payment_value", "sum"),
            orders=("order_id", "count"),
            unique_customers=("customer_unique_id", "nunique"),
        )
        .sort_values("gmv", ascending=False)
    )
    states["share_pct"] = states["gmv"] / states["gmv"].sum() * 100

    delivered_payments = tables["payments"].loc[
        tables["payments"]["order_id"].isin(delivered_ids)
    ]
    payment_mix = (
        delivered_payments.groupby("payment_type", as_index=False)
        .agg(
            payment_value=("payment_value", "sum"),
            orders=("order_id", "nunique"),
            average_installments=("payment_installments", "mean"),
        )
        .sort_values("payment_value", ascending=False)
    )
    payment_mix["share_pct"] = (
        payment_mix["payment_value"] / payment_mix["payment_value"].sum() * 100
    )

    delivery_groups = (
        delivered.dropna(subset=["is_late_delivery"])
        .assign(
            delivery_group=lambda data: np.where(
                data["is_late_delivery"].eq(1), "late", "on_time_or_early"
            )
        )
        .groupby("delivery_group", as_index=False)
        .agg(
            orders=("order_id", "count"),
            average_delivery_days=("delivery_days", "mean"),
            average_review_score=("average_review_score", "mean"),
        )
    )

    state_delivery = (
        delivered.groupby("customer_state", as_index=False)
        .agg(
            orders=("order_id", "count"),
            late_delivery_rate=("is_late_delivery", "mean"),
            average_review_score=("average_review_score", "mean"),
        )
        .query("orders >= 100")
        .sort_values("late_delivery_rate", ascending=False)
        .head(4)
    )

    customer_orders = (
        delivered.groupby("customer_unique_id", as_index=False)
        .agg(delivered_orders=("order_id", "count"))
    )
    repeat_customers = int(customer_orders["delivered_orders"].gt(1).sum())
    repeat_rate = repeat_customers / len(customer_orders) * 100

    first_orders = (
        delivered.sort_values(
            ["customer_unique_id", "order_purchase_timestamp", "order_id"]
        )
        .groupby("customer_unique_id", as_index=False)
        .first()[["customer_unique_id", "is_late_delivery"]]
        .merge(customer_orders, on="customer_unique_id", validate="one_to_one")
    )
    first_orders["is_repeat"] = first_orders["delivered_orders"].gt(1)
    retention_by_first_delivery = (
        first_orders.dropna(subset=["is_late_delivery"])
        .groupby("is_late_delivery", as_index=False)
        .agg(
            customers=("customer_unique_id", "count"),
            repeat_customers=("is_repeat", "sum"),
            repeat_rate=("is_repeat", "mean"),
        )
    )

    yoy = (
        delivered.loc[
            delivered["order_purchase_timestamp"].dt.year.isin([2017, 2018])
            & delivered["order_purchase_timestamp"].dt.month.le(8)
        ]
        .assign(year=lambda data: data["order_purchase_timestamp"].dt.year)
        .groupby("year", as_index=False)
        .agg(gmv=("payment_value", "sum"), orders=("order_id", "count"))
    )
    gmv_2017 = float(yoy.loc[yoy["year"].eq(2017), "gmv"].iloc[0])
    gmv_2018 = float(yoy.loc[yoy["year"].eq(2018), "gmv"].iloc[0])
    yoy_growth = (gmv_2018 - gmv_2017) / gmv_2017 * 100

    review_distribution = (
        delivered.dropna(subset=["average_review_score"])
        .assign(review_score=lambda data: data["average_review_score"].round().astype(int))
        .groupby("review_score", as_index=False)
        .agg(reviews=("order_id", "count"))
    )
    review_distribution["share_pct"] = (
        review_distribution["reviews"] / review_distribution["reviews"].sum() * 100
    )
    positive_review_share = float(
        review_distribution.loc[
            review_distribution["review_score"].isin([4, 5]), "share_pct"
        ].sum()
    )

    on_time = delivery_groups.loc[
        delivery_groups["delivery_group"].eq("on_time_or_early")
    ].iloc[0]
    late = delivery_groups.loc[delivery_groups["delivery_group"].eq("late")].iloc[0]

    on_time_retention = retention_by_first_delivery.loc[
        retention_by_first_delivery["is_late_delivery"].eq(0)
    ].iloc[0]
    late_retention = retention_by_first_delivery.loc[
        retention_by_first_delivery["is_late_delivery"].eq(1)
    ].iloc[0]

    raw_files = sorted((PROJECT_DIR / "data" / "raw").glob("*.csv"))
    source_rows = (
        sum(len(pd.read_csv(path, low_memory=False)) for path in raw_files)
        if raw_files
        else sum(len(table) for table in tables.values())
    )

    payload: dict[str, object] = {
        "meta": {
            "dataThrough": "Aug 2018",
            "sourceFiles": 9,
            "sourceRows": source_rows,
            "deliveredOrderRows": int(len(delivered)),
        },
        "kpis": {
            "deliveredGmv": _round(delivered["payment_value"].sum()),
            "deliveredOrders": int(len(delivered)),
            "uniqueCustomers": int(delivered["customer_unique_id"].nunique()),
            "averageOrderValue": _round(delivered["payment_value"].mean()),
            "lateDeliveryRate": _round(delivered["is_late_delivery"].mean() * 100),
            "lateOrders": int(delivered["is_late_delivery"].eq(1).sum()),
            "knownDeliveryDateOrders": int(delivered["is_late_delivery"].notna().sum()),
            "averageReviewScore": _round(delivered["average_review_score"].mean()),
            "positiveReviewShare": _round(positive_review_share, 1),
            "yoyGmvGrowth": _round(yoy_growth, 1),
            "comparableGmv2017": _round(gmv_2017),
            "comparableGmv2018": _round(gmv_2018),
            "repeatCustomerRate": _round(repeat_rate),
            "repeatCustomers": repeat_customers,
        },
        "monthly": [
            {
                "month": pd.Period(row.purchase_month).strftime("%b %y"),
                "gmv": _round(row.gmv),
                "orders": int(row.orders),
            }
            for row in monthly.itertuples(index=False)
        ],
        "categories": [
            {
                "name": str(row.category).replace("_", " ").title(),
                "productValue": _round(row.product_value),
                "orders": int(row.orders),
            }
            for row in categories.itertuples(index=False)
        ],
        "states": [
            {
                "code": str(row.customer_state),
                "gmv": _round(row.gmv),
                "orders": int(row.orders),
                "uniqueCustomers": int(row.unique_customers),
                "sharePct": _round(row.share_pct, 1),
            }
            for row in states.head(5).itertuples(index=False)
        ],
        "paymentMix": [
            {
                "type": str(row.payment_type),
                "paymentValue": _round(row.payment_value),
                "orders": int(row.orders),
                "sharePct": _round(row.share_pct, 1),
                "averageInstallments": _round(row.average_installments, 1),
            }
            for row in payment_mix.itertuples(index=False)
        ],
        "delivery": {
            "onTimeOrEarly": {
                "orders": int(on_time.orders),
                "averageDeliveryDays": _round(on_time.average_delivery_days, 1),
                "averageReviewScore": _round(on_time.average_review_score, 2),
            },
            "late": {
                "orders": int(late.orders),
                "averageDeliveryDays": _round(late.average_delivery_days, 1),
                "averageReviewScore": _round(late.average_review_score, 2),
            },
            "reviewGap": _round(
                on_time.average_review_score - late.average_review_score, 2
            ),
            "priorityStates": [
                {
                    "code": str(row.customer_state),
                    "orders": int(row.orders),
                    "lateDeliveryRate": _round(row.late_delivery_rate * 100, 1),
                    "averageReviewScore": _round(row.average_review_score, 2),
                }
                for row in state_delivery.itertuples(index=False)
            ],
        },
        "retention": {
            "overallRepeatRate": _round(repeat_rate),
            "firstOrderOnTimeRepeatRate": _round(on_time_retention.repeat_rate * 100),
            "firstOrderLateRepeatRate": _round(late_retention.repeat_rate * 100),
            "differencePoints": _round(
                (on_time_retention.repeat_rate - late_retention.repeat_rate) * 100,
                2,
            ),
        },
    }

    return payload


def main() -> None:
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"DASHBOARD_DATA_OK|{OUTPUT_FILE.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()
