import { test } from "node:test";
import assert from "node:assert/strict";
import { cohortSummary, matches, summarize, wilson, type OrderBin } from "./delivery-metrics.ts";

const base = { purchase_month: "2018-01", customer_state: "SP", primary_category: "books", gmv: 0, gmv_known: 0, delivery_days_sum: 0 };
test("weighted reviews and late-rate denominators exclude missing observations", () => {
  const rows: OrderBin[] = [
    { ...base, delivery_status: "late", orders: 10, reviewed: 1, review_sum: 1 },
    { ...base, delivery_status: "late", orders: 10, reviewed: 9, review_sum: 45 },
    { ...base, delivery_status: "on_time", orders: 80, reviewed: 40, review_sum: 160 },
    { ...base, delivery_status: "unknown", orders: 100, reviewed: 1, review_sum: 5 },
  ];
  const result = summarize(rows);
  assert.equal(result.lateRate, .2);
  assert.equal(result.lateReview, 4.6);
  assert.equal(result.onTimeReview, 4);
  assert.equal(summarize([]).reviewGap, null);
});
test("cohort rates exclude customers without a full follow-up window", () => {
  const result = cohortSummary([{ ...base, first_delivery_status: "late", customers: 100, eligible_customers: 20, repeat_customers: 2 }], "late");
  assert.equal(result.rate, .1);
  assert.equal(cohortSummary([], "late").rate, null);
  assert.equal(wilson(0, 0), null);
  assert.ok(wilson(0, 100)![1] > 0);
});
test("filters apply month, state and primary category together", () => {
  assert.equal(matches(base, { from: "2018-01", to: "2018-01", state: "SP", category: "books" }), true);
  assert.equal(matches(base, { from: "2018-02", to: "2018-03", state: "", category: "" }), false);
  assert.equal(matches(base, { from: "2018-01", to: "2018-01", state: "RJ", category: "books" }), false);
});
