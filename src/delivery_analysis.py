"""Order-grain delivery analysis and a fully observed repeat-purchase cohort."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AS_OF = "2018-08-31"
HORIZON_DAYS = 90


def classify_delivery(delivered, promised):
    actual = pd.to_datetime(delivered, errors="coerce", format="mixed").dt.normalize()
    estimate = pd.to_datetime(promised, errors="coerce", format="mixed").dt.normalize()
    result = pd.Series("unknown", index=actual.index, dtype="string")
    known = actual.notna() & estimate.notna()
    result.loc[known & actual.le(estimate)] = "on_time"
    result.loc[known & actual.gt(estimate)] = "late"
    return result


def build_facts(processed: Path, as_of=DEFAULT_AS_OF, horizon_days=HORIZON_DAYS):
    cutoff = pd.Timestamp(as_of).normalize() + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    orders = pd.read_csv(processed / "olist_orders.csv")
    for column in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[column] = pd.to_datetime(orders[column], errors="coerce", format="mixed")
    orders = orders.loc[
        orders.order_status.eq("delivered") & orders.order_purchase_timestamp.le(cutoff)
        & orders.order_delivered_customer_date.le(cutoff)
    ].copy()
    if orders.order_id.duplicated().any():
        raise ValueError("Duplicate order IDs")
    if orders.order_purchase_timestamp.gt(orders.order_delivered_customer_date).any():
        raise ValueError("Delivery precedes purchase")
    customers = pd.read_csv(processed / "olist_customers.csv")
    products = pd.read_csv(processed / "olist_products.csv")
    items = pd.read_csv(processed / "olist_order_items.csv")
    payments = pd.read_csv(processed / "olist_order_payments.csv")
    reviews = pd.read_csv(processed / "olist_order_reviews.csv")
    items = items.merge(products[["product_id", "product_category_name_english"]], on="product_id", how="left", validate="many_to_one")
    items["category"] = items.product_category_name_english.fillna("unknown")
    categories = items.groupby(["order_id", "category"], as_index=False).agg(product_value=("price", "sum"))
    primary = categories.sort_values(["order_id", "product_value", "category"], ascending=[True, False, True]).drop_duplicates("order_id")
    primary = primary.rename(columns={"category": "primary_category"})[["order_id", "primary_category"]]
    payments = payments.groupby("order_id", as_index=False).agg(gmv=("payment_value", "sum"))
    answered = pd.to_datetime(reviews.review_answer_timestamp, errors="coerce", format="mixed")
    reviews = reviews.loc[answered.le(cutoff) & reviews.review_score.between(1, 5)]
    reviews = reviews.groupby("order_id", as_index=False).agg(review_score=("review_score", "mean"))
    fact = (orders.merge(customers[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id", how="left", validate="one_to_one")
            .merge(primary, on="order_id", how="left", validate="one_to_one")
            .merge(payments, on="order_id", how="left", validate="one_to_one")
            .merge(reviews, on="order_id", how="left", validate="one_to_one"))
    if fact.customer_unique_id.isna().any():
        raise ValueError("Delivered orders need a customer identity for cohort analysis")
    fact["primary_category"] = fact.primary_category.fillna("unknown")
    fact["customer_state"] = fact.customer_state.fillna("unknown")
    fact["delivery_status"] = classify_delivery(fact.order_delivered_customer_date, fact.order_estimated_delivery_date)
    fact["purchase_month"] = fact.order_purchase_timestamp.dt.strftime("%Y-%m")
    fact["delivery_days"] = (fact.order_delivered_customer_date - fact.order_purchase_timestamp).dt.total_seconds() / 86400
    fact["delay_days"] = (fact.order_delivered_customer_date.dt.normalize() - fact.order_estimated_delivery_date.dt.normalize()).dt.total_seconds() / 86400
    first = fact.sort_values(["customer_unique_id", "order_purchase_timestamp", "order_id"]).drop_duplicates("customer_unique_id").copy()
    first = first.rename(columns={"order_purchase_timestamp": "first_purchase_at", "delivery_status": "first_delivery_status"})
    first["eligible"] = first.first_purchase_at.add(pd.Timedelta(days=horizon_days)).le(cutoff)
    follow = fact[["customer_unique_id", "order_id", "order_purchase_timestamp"]].merge(first[["customer_unique_id", "first_purchase_at"]], on="customer_unique_id", validate="many_to_one")
    repeated = follow.loc[follow.order_purchase_timestamp.gt(follow.first_purchase_at) & follow.order_purchase_timestamp.le(follow.first_purchase_at + pd.Timedelta(days=horizon_days)), "customer_unique_id"]
    first["repeat_within_window"] = first.customer_unique_id.isin(repeated) & first.eligible
    return fact, first


def aggregate(fact, cohorts, as_of=DEFAULT_AS_OF, horizon_days=HORIZON_DAYS):
    fact = fact.assign(reviewed=fact.review_score.notna().astype(int), gmv_known=fact.gmv.notna().astype(int), review_sum=fact.review_score.fillna(0))
    rows = fact.groupby(["purchase_month", "customer_state", "primary_category", "delivery_status"], as_index=False).agg(
        orders=("order_id", "count"), reviewed=("reviewed", "sum"), review_sum=("review_sum", "sum"),
        gmv=("gmv", "sum"), gmv_known=("gmv_known", "sum"), delivery_days_sum=("delivery_days", "sum"))
    cohort_rows = cohorts.groupby(["purchase_month", "customer_state", "primary_category", "first_delivery_status"], as_index=False).agg(
        customers=("customer_unique_id", "count"), eligible_customers=("eligible", "sum"), repeat_customers=("repeat_within_window", "sum"))
    numeric = rows.select_dtypes(include="number").columns
    rows[numeric] = rows[numeric].round(6)
    return {
        "meta": {"asOf": as_of, "horizonDays": horizon_days, "orders": len(fact), "customers": len(cohorts),
                 "eligibleCustomers": int(cohorts.eligible.sum()), "reviewedOrders": int(fact.reviewed.sum()),
                 "lateRule": "Delivery calendar date after promised calendar date",
                 "categoryRule": "Largest summed product value per order; alphabetical tie-break",
                 "repeatRule": "Another delivered order purchased after the first purchase and within 90 days; both deliveries observed by cutoff",
                 "cohortFilterRule": "Filters describe the customer's first delivered order in available history"},
        "months": sorted(fact.purchase_month.unique().tolist()),
        "states": sorted(fact.customer_state.unique().tolist()),
        "categories": sorted(fact.primary_category.unique().tolist()),
        "orders": rows.to_dict(orient="records"), "cohorts": cohort_rows.to_dict(orient="records"),
    }


def export(processed=None, output=None, powerbi_dir=None, as_of=DEFAULT_AS_OF):
    processed = Path(processed or ROOT / "data/processed")
    output = Path(output or ROOT / "dashboard/public/delivery-data.json")
    fact, first = build_facts(processed, as_of=as_of)
    payload = aggregate(fact, first, as_of=as_of)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    folder = Path(powerbi_dir or ROOT / "powerbi/data")
    folder.mkdir(parents=True, exist_ok=True)
    fact[["order_id", "customer_unique_id", "order_purchase_timestamp", "purchase_month", "customer_state", "primary_category", "delivery_status", "delivery_days", "delay_days", "review_score", "gmv"]].to_csv(folder / "fact_orders.csv", index=False)
    first[["customer_unique_id", "first_purchase_at", "purchase_month", "customer_state", "primary_category", "first_delivery_status", "eligible", "repeat_within_window"]].to_csv(folder / "customer_cohorts.csv", index=False)
    print(f"DELIVERY_ANALYSIS_OK|orders={len(fact)}|eligible_customers={int(first.eligible.sum())}")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--powerbi-dir", type=Path)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF)
    args = parser.parse_args()
    export(args.processed, args.output, args.powerbi_dir, args.as_of)
