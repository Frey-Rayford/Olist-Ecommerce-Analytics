import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.delivery_analysis import aggregate, build_facts, classify_delivery, export


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        events = [
            ("a1", "A", "2018-01-01", "2018-01-05 20:00", "2018-01-05"),
            ("a2", "A", "2018-04-01", "2018-04-05", "2018-04-05"),
            ("b1", "B", "2018-01-10", "2018-01-20", "2018-01-19"),
            ("b2", "B", "2018-04-11", "2018-04-15", "2018-04-15"),
            ("c1", "C", "2018-06-15", "2018-06-20", "2018-06-20"),
            ("c2", "C", "2018-07-01", "2018-07-05", "2018-07-05"),
            ("d1", "D", "2018-01-01", "2018-01-05", None),
            ("e1", "E", "2018-08-30", "2018-09-02", "2018-09-02"),
        ]
        orders, customers, items, payments = [], [], [], []
        for key, customer, purchase, actual, promised in events:
            orders.append(dict(order_id=key, customer_id=key, order_status="delivered", order_purchase_timestamp=purchase, order_delivered_customer_date=actual, order_estimated_delivery_date=promised))
            customers.append(dict(customer_id=key, customer_unique_id=customer, customer_state="SP"))
            items.append(dict(order_id=key, product_id="p1", price=50))
            payments.append(dict(order_id=key, payment_value=60))
        # Multiple items and payment rows must not multiply an order's review.
        items.extend([dict(order_id="a1", product_id="p1", price=25), dict(order_id="a1", product_id="p2", price=75)])
        payments.append(dict(order_id="a1", payment_value=10))
        tables = {
            "olist_orders": orders, "olist_customers": customers, "olist_order_items": items,
            "olist_order_payments": payments,
            "olist_products": [dict(product_id="p1", product_category_name_english="alpha"), dict(product_id="p2", product_category_name_english="beta")],
            "olist_order_reviews": [dict(order_id="a1", review_score=2, review_answer_timestamp="2018-01-06"), dict(order_id="a1", review_score=4, review_answer_timestamp="2018-01-07"), dict(order_id="b1", review_score=1, review_answer_timestamp="2018-09-01")],
        }
        for name, rows in tables.items():
            pd.DataFrame(rows).to_csv(self.folder / f"{name}.csv", index=False)

    def test_same_day_is_on_time_and_missing_promise_is_unknown(self):
        result = classify_delivery(pd.Series(["2018-01-05 20:00", "2018-01-06 00:00", "2018-01-01"]), pd.Series(["2018-01-05", "2018-01-05", None]))
        self.assertEqual(result.tolist(), ["on_time", "late", "unknown"])

    def test_order_grain_review_cutoff_and_category_tie(self):
        fact, _ = build_facts(self.folder)
        self.assertEqual(len(fact), 7)
        self.assertTrue(fact.order_id.is_unique)
        row = fact.set_index("order_id").loc["a1"]
        self.assertEqual(row.review_score, 3)
        self.assertEqual(row.gmv, 70)
        self.assertEqual(row.primary_category, "alpha")
        self.assertTrue(pd.isna(fact.set_index("order_id").loc["b1"].review_score))

    def test_repeat_window_boundary_and_right_censoring(self):
        _, cohort = build_facts(self.folder)
        customers = cohort.set_index("customer_unique_id")
        self.assertTrue(customers.loc["A"].repeat_within_window)
        self.assertFalse(customers.loc["B"].repeat_within_window)
        self.assertFalse(customers.loc["C"].eligible)
        self.assertFalse(customers.loc["C"].repeat_within_window)
        self.assertNotIn("E", customers.index)

    def test_bins_reconcile_and_exports_are_valid_json(self):
        fact, first = build_facts(self.folder)
        data = aggregate(fact, first)
        self.assertEqual(sum(row["orders"] for row in data["orders"]), len(fact))
        self.assertEqual(sum(row["eligible_customers"] for row in data["cohorts"]), int(first.eligible.sum()))
        self.assertAlmostEqual(sum(row["gmv"] for row in data["orders"]), fact.gmv.sum())
        json.dumps(data, allow_nan=False)
        export(self.folder, self.folder / "analysis.json", self.folder / "powerbi")
        self.assertTrue((self.folder / "powerbi/customer_cohorts.csv").exists())


if __name__ == "__main__":
    unittest.main()
