import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from src import build_processed_data as build
from src import validate_processed_data as validate
from src import export_dashboard_data as export

FIXTURE = Path(__file__).parent / 'fixtures/raw'


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.processed = Path(self.tmp.name)
        with patch.object(build, 'RAW_DIR', FIXTURE), patch.object(build, 'PROCESSED_DIR', self.processed):
            build.main()
        self.counts = {p.name: len(pd.read_csv(p)) for p in self.processed.glob('*.csv')}

    def test_cleaning_does_not_mark_same_day_evening_delivery_late(self):
        import shutil
        raw = self.processed / 'raw'
        shutil.copytree(FIXTURE, raw)
        orders = pd.read_csv(raw / 'olist_orders_dataset.csv')
        promise = pd.Timestamp(orders.loc[0, 'order_estimated_delivery_date'])
        orders.loc[0, 'order_delivered_customer_date'] = str(promise + pd.Timedelta(hours=20))
        orders.to_csv(raw / 'olist_orders_dataset.csv', index=False)
        with patch.object(build, 'RAW_DIR', raw), patch.object(build, 'PROCESSED_DIR', self.processed):
            build.main()
        cleaned = pd.read_csv(self.processed / 'olist_orders.csv')
        self.assertEqual(cleaned.loc[0, 'is_late_delivery'], 0)
        self.assertEqual(cleaned.loc[0, 'delivery_delay_days'], 0)

    def test_fixture_runs_through_cleaning_relationship_checks_and_export(self):
        validate.main(self.processed, self.counts)
        with patch.object(export, 'PROCESSED_DIR', self.processed), patch.object(export, 'PROJECT_DIR', self.processed):
            payload = export.build_payload()
        orders = pd.read_csv(self.processed / 'olist_orders.csv')
        payments = pd.read_csv(self.processed / 'olist_order_payments.csv')
        delivered_ids = orders.loc[orders.order_status.eq('delivered'), 'order_id']
        expected_gmv = payments.loc[payments.order_id.isin(delivered_ids), 'payment_value'].sum()
        self.assertAlmostEqual(payload['kpis']['deliveredGmv'], expected_gmv, places=2)
        self.assertEqual(payload['kpis']['deliveredOrders'], len(delivered_ids))
        self.assertEqual(payload['delivery']['late']['orders'] + payload['delivery']['onTimeOrEarly']['orders'], len(delivered_ids))
        json.dumps(payload, allow_nan=False)

    def test_multiple_items_and_payments_do_not_multiply_gmv(self):
        path = self.processed / 'olist_order_items.csv'
        items = pd.read_csv(path)
        extra = items.iloc[[0]].copy()
        extra['order_item_id'] = 99
        pd.concat([items, extra], ignore_index=True).to_csv(path, index=False)
        path = self.processed / 'olist_order_payments.csv'
        payments = pd.read_csv(path)
        extra = payments.iloc[[0]].copy()
        extra['payment_sequential'] = 99
        extra['payment_value'] = 10
        payments = pd.concat([payments, extra], ignore_index=True)
        payments.to_csv(path, index=False)
        with patch.object(export, 'PROCESSED_DIR', self.processed), patch.object(export, 'PROJECT_DIR', self.processed):
            summary, _ = export._load_order_summary()
        order = summary.loc[summary.order_id.eq(extra.iloc[0].order_id)].iloc[0]
        expected = payments.loc[payments.order_id.eq(order.order_id), 'payment_value'].sum()
        self.assertAlmostEqual(order.payment_value, expected)
        self.assertTrue(summary.order_id.is_unique)

    def test_unknown_order_fails_validation(self):
        path = self.processed / 'olist_order_items.csv'
        items = pd.read_csv(path)
        items.loc[0, 'order_id'] = 'missing-order'
        items.to_csv(path, index=False)
        with self.assertRaisesRegex(AssertionError, 'unknown order_id'):
            validate.main(self.processed, self.counts)

    def test_duplicate_item_key_fails_validation(self):
        path = self.processed / 'olist_order_items.csv'
        items = pd.read_csv(path)
        items = pd.concat([items, items.iloc[[0]]], ignore_index=True)
        items.to_csv(path, index=False)
        self.counts[path.name] += 1
        with self.assertRaisesRegex(AssertionError, 'composite key'):
            validate.main(self.processed, self.counts)


if __name__ == '__main__':
    unittest.main()
