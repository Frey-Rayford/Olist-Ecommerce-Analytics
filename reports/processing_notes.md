# Processing notes

Processing definition updated: 2026-11-04

## Generated outputs

`src/build_processed_data.py` creates nine files in `data/processed/`.

| Processed file | Rows | Main transformation |
|---|---:|---|
| `olist_customers.csv` | 99,441 | ZIP prefixes stored as five-character strings |
| `olist_geolocation_by_zip.csv` | 19,015 | Aggregated to one row per ZIP prefix |
| `olist_order_items.csv` | 112,650 | Parsed dates; added `item_total_value` |
| `olist_order_payments.csv` | 103,886 | Standardized text fields |
| `olist_order_reviews.csv` | 99,224 | Parsed dates; added `has_review_comment` |
| `olist_orders.csv` | 99,441 | Parsed dates; added delivery-duration metrics |
| `olist_products.csv` | 32,951 | Corrected source column names; added English category |
| `olist_sellers.csv` | 3,095 | ZIP prefixes stored as five-character strings |
| `product_category_name_translation.csv` | 71 | Standardized text fields |

## Processing principles

- Raw files are read-only and never overwritten.
- Rows are not removed only because comments, delivery dates, location attributes, or translations are missing.
- Source identifiers are preserved for traceability.
- Geolocation coordinates are averaged by ZIP prefix; city and state use the most frequent non-null value.
- Missing English category names fall back to the Portuguese source value.
- Boolean fields are exported as `1/0` for SQL Server `BIT` compatibility.
- Payments, items, and reviews are aggregated independently before order-level analysis.

## Quality checks

`src/validate_processed_data.py` verifies:

- All nine processed files exist with expected row counts.
- Primary and composite keys remain unique.
- Required order, product, and seller relationships have no orphan rows.
- Customer and seller ZIP prefixes retain five characters.
- `item_total_value = price + freight_value` for every order item.
- Corrected product column names are present.
- Boolean values are SQL-compatible.

Successful result:

```text
CHECKS_OK|files=9|orders=99441|items=112650
```

## Delivery snapshot

Delivery delay compares calendar dates. Missing actual or estimated delivery dates keep an unknown flag; they are excluded from late-rate denominators. The snapshot module additionally requires delivery by its cutoff and excludes reviews answered later.

The primary category is selected after summing item prices within each order-category pair, with alphabetical tie-breaking. Payments and reviews are aggregated separately. A cohort customer is eligible only after 90 days from the first visible delivered-order purchase; later purchases are measured within that window and must also be delivered by the cutoff.
