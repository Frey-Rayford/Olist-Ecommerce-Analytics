"""Write the case study from the same facts used by the dashboard."""
import json
import math
from pathlib import Path

try:
    from .delivery_analysis import DEFAULT_AS_OF, ROOT, build_facts
except ImportError:
    from delivery_analysis import DEFAULT_AS_OF, ROOT, build_facts


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    divisor = 1 + z*z/total
    center = (p + z*z/(2*total))/divisor
    width = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total))/divisor
    return [max(0, center-width), min(1, center+width)]


def write_report(processed=None, output_dir=None):
    fact, cohort = build_facts(Path(processed or ROOT / "data/processed"))
    output = Path(output_dir or ROOT / "reports")
    output.mkdir(parents=True, exist_ok=True)
    known = fact.delivery_status.ne("unknown")
    late = fact.delivery_status.eq("late")
    on_time = fact.delivery_status.eq("on_time")
    states = fact.assign(late=late.astype(int), known=known.astype(int)).groupby("customer_state").agg(late=("late", "sum"), known=("known", "sum")).sort_values("late", ascending=False)
    groups = {}
    for status in ["on_time", "late", "unknown"]:
        selected = cohort.loc[cohort.first_delivery_status.eq(status)]
        eligible = selected.loc[selected.eligible]
        repeated = int(eligible.repeat_within_window.sum())
        groups[status] = {"customers": len(selected), "eligible": len(eligible), "repeated": repeated,
                          "repeat_rate": repeated/len(eligible) if len(eligible) else None,
                          "wilson_95": wilson(repeated, len(eligible))}
    findings = {"snapshot": DEFAULT_AS_OF, "orders": len(fact), "known_delivery_dates": int(known.sum()),
                "late_orders": int(late.sum()), "late_rate": float(late.sum()/known.sum()),
                "late_review": float(fact.loc[late, "review_score"].mean()),
                "on_time_review": float(fact.loc[on_time, "review_score"].mean()),
                "late_reviewed_orders": int(fact.loc[late, "review_score"].notna().sum()),
                "on_time_reviewed_orders": int(fact.loc[on_time, "review_score"].notna().sum()),
                "newer_customers_excluded": int((~cohort.eligible).sum()), "cohorts": groups,
                "top_states_by_late_orders": [{"state": state, "late": int(row.late), "known": int(row.known), "late_rate": float(row.late/row.known)} for state, row in states.head(5).iterrows()]}
    (output / "delivery_findings.json").write_text(json.dumps(findings, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    top = ", ".join(f"{item['state']} ({item['late']:,} late / {item['known']:,} known-date orders; {item['late_rate']:.2%})" for item in findings["top_states_by_late_orders"][:3])
    def cohort_text(status):
        row = groups[status]
        if row["repeat_rate"] is None:
            return "No eligible customers."
        lower, upper = row["wilson_95"]
        return f"{row['repeated']:,} / {row['eligible']:,} eligible customers ({row['repeat_rate']:.2%}; 95% Wilson interval {lower:.2%}–{upper:.2%})."
    case = f'''# Delivery delays and repeat purchase

## Question

Which segments account for the most late orders, and how do reviews and repeat purchases differ between delivery groups?

## Scope

Olist public data, using purchases and completed deliveries observed by {DEFAULT_AS_OF}: {len(fact):,} orders. The overview uses the final delivered-order dataset; this analysis uses a snapshot, so totals differ. Reviews answered after the cutoff are excluded.

## Results

- Late deliveries: {int(late.sum()):,} / {int(known.sum()):,} orders with known dates ({findings['late_rate']:.2%}).
- Mean review: {findings['late_review']:.2f}/5 for late orders ({findings['late_reviewed_orders']:,} reviewed orders), versus {findings['on_time_review']:.2f}/5 for on-time orders ({findings['on_time_reviewed_orders']:,} reviewed orders).
- Largest late-order counts: {top}.
- First order on time, repeat within 90 days: {cohort_text('on_time')}
- First order late, repeat within 90 days: {cohort_text('late')}
- {findings['newer_customers_excluded']:,} newer customers excluded: 90 days have not elapsed.

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
'''
    (output / "delivery_case_study.md").write_text(case, encoding="utf-8")
    print("DELIVERY_REPORT_OK")
    return findings


if __name__ == "__main__":
    write_report()
