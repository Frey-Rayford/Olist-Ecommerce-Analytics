# SQL KPI results

Last validated: 2026-08-06  
Engine: SQL Server 2019  
Database: `olist_analytics`

## Data-quality result

- All nine tables match expected row counts.
- Primary and composite key checks return no duplicates.
- Required order, product, seller, payment, and review relationships return no orphan rows.
- Product prices and freight values contain no negative values.
- `item_total_value` is correctly calculated.
- No delivered order has a customer-delivery date before its purchase date.

## Executive KPIs

Scope: orders with `order_status = 'delivered'`.

| KPI | Result |
|---|---:|
| Delivered orders | 96,478 |
| Unique customers | 93,358 |
| Product value | R$13,221,498.11 |
| Freight value | R$2,198,275.64 |
| Delivered GMV | R$15,422,461.77 |
| Average order value | R$159.85 |
| Average delivery time | 12.56 days |
| Late-delivery rate | 8.11% |
| Average review score | 4.16/5 |

Delivered GMV is the total customer payment value for delivered orders and includes freight. Product value excludes freight.

## Findings

### 1. Strong growth in the comparable period

| Year, Jan–Aug | Delivered orders | Delivered GMV |
|---|---:|---:|
| 2017 | 21,998 | R$3,473,862.76 |
| 2018 | 52,783 | R$8,452,975.20 |

Comparable delivered GMV increased **143.33%**. The sparse 2016 period is excluded from the growth baseline.

### 2. Late delivery is associated with materially lower satisfaction

| Delivery group | Orders | Average delivery | Average review |
|---|---:|---:|---:|
| On time or early | 88,644 | 10.88 days | 4.29 |
| Late | 7,826 | 31.52 days | 2.57 |

Late orders average **1.73 fewer review points**. This is a descriptive association and does not establish causality.

### 3. Commercial value is geographically concentrated

- São Paulo generated R$5.77M, approximately **37.4%** of delivered GMV.
- SP, RJ, and MG together generated approximately **62.5%**.
- AL, MA, PI, and CE had the highest late-delivery rates among states with at least 100 delivered orders.

### 4. Leading product categories

| Category | Delivered product value |
|---|---:|
| health_beauty | R$1,233,131.72 |
| watches_gifts | R$1,166,176.98 |
| bed_bath_table | R$1,023,434.76 |
| sports_leisure | R$954,852.55 |
| computers_accessories | R$888,724.61 |

`health_beauty` generated the most product value, while `bed_bath_table` had the largest order count among the five leaders.

### 5. Repeat purchasing is uncommon

- Customers with at least one delivered order: 93,358.
- Customers with more than one delivered order: 2,801.
- Repeat-customer rate: **3.00%**.
- Repeat rate after an on-time or early first order: **3.04%**.
- Repeat rate after a late first order: **2.52%**.

The retention difference is observational and should be tested with additional customer, campaign, and service data.

### 6. Payment value is credit-card led

- Credit card: **78.5%** of delivered payment value.
- Boleto: **18.0%**.
- Voucher and debit card: approximately **3.6%** combined.

## Recommended next analyses

1. Measure late-order volume and rate jointly by state, seller, and category.
2. Separate high-volume operational problems from small high-rate segments.
3. Explore whether freight burden is associated with reviews or repeat behavior.
4. Segment first-to-second purchase conversion by acquisition cohort and category.
