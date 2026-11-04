# Delivery delays and repeat purchase

## Question

Which segments account for the most late orders, and how do reviews and repeat purchases differ between delivery groups?

## Scope

Olist public data, using purchases and completed deliveries observed by 2018-08-31: 96,411 orders. The overview uses the final delivered-order dataset; this analysis uses a snapshot, so totals differ. Reviews answered after the cutoff are excluded.

## Results

- Late deliveries: 6,475 / 96,411 orders with known dates (6.72%).
- Mean review: 2.27/5 for late orders (6,306 reviewed orders), versus 4.29/5 for on-time orders (88,818 reviewed orders).
- Largest late-order counts: SP (1,800 late / 40,474 known-date orders; 4.45%), RJ (1,483 late / 12,338 known-date orders; 12.02%), MG (513 late / 11,348 known-date orders; 4.52%).
- First order on time, repeat within 90 days: 1,418 / 70,002 eligible customers (2.03%; 95% Wilson interval 1.92%–2.13%).
- First order late, repeat within 90 days: 101 / 5,696 eligible customers (1.77%; 95% Wilson interval 1.46%–2.15%).
- 17,595 newer customers excluded: 90 days have not elapsed.

## What I would investigate

Start with states contributing the most late orders, then narrow by primary category. Check both count and rate: a large market can create many delays while a small market has a higher rate. Neither ranking alone identifies a carrier or seller problem.

Ask for carrier, service level, seller handling time and shipping cost before changing a delivery process. A pilot should define its comparison group and observation window first, then track timeliness, review coverage, cost and repeat purchases together. These group differences do not establish a causal effect of delays.

## Definitions

- Late means the delivery calendar date is after the promised calendar date. An evening delivery on the promised day is on time.
- Primary category is the highest summed product value within an order, with an alphabetical tie-break. Each order belongs to one category.
- Each order contributes one average review, avoiding multiplication by items, payments or reviews. Missing reviews stay out of score denominators.
- Repeat means a strictly later purchase within 90 days of the first purchase, with both orders delivered by the cutoff. First purchase means the first delivered order visible in this dataset, not necessarily the customer's first-ever purchase.
- Only first purchases with a full 90-day follow-up enter the repeat-rate denominator. Filters describe that first order's month, state and primary category.
- Wilson intervals describe sampling variability, not confounding or causality.

## Reproduce

Run `python src/run_pipeline.py` after adding the raw CSVs. The dashboard reads `dashboard/public/delivery-data.json`; Power BI imports the CSVs in `powerbi/data/`. Exact counts are saved in `reports/delivery_findings.json`. T-SQL equivalents are in `sql/07_delivery_retention.sql`; run them against a refreshed SQL model to verify parity in your SQL Server environment.

## Correction to the earlier version

The timestamp comparison marked 1,292 same-day deliveries as late. On the full delivered-order dataset, the corrected rate is 6,534 / 96,470 known-date orders = 6.77%, replacing 8.11%. Current data and tests use the calendar-day definition.
