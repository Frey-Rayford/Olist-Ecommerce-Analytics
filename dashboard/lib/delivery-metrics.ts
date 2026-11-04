export type OrderBin = { purchase_month: string; customer_state: string; primary_category: string; delivery_status: string; orders: number; reviewed: number; review_sum: number; gmv: number; gmv_known: number; delivery_days_sum: number };
export type CohortBin = { purchase_month: string; customer_state: string; primary_category: string; first_delivery_status: string; customers: number; eligible_customers: number; repeat_customers: number };
export type DeliveryData = { meta: { asOf: string; horizonDays: number; orders: number; eligibleCustomers: number; reviewedOrders: number }; months: string[]; states: string[]; categories: string[]; orders: OrderBin[]; cohorts: CohortBin[] };
export type Filters = { from: string; to: string; state: string; category: string };

export function matches(row: Pick<OrderBin, "purchase_month" | "customer_state" | "primary_category">, filters: Filters) {
  return row.purchase_month >= filters.from && row.purchase_month <= filters.to && (!filters.state || row.customer_state === filters.state) && (!filters.category || row.primary_category === filters.category);
}

export function ratio(numerator: number, denominator: number) {
  return denominator > 0 ? numerator / denominator : null;
}

export function summarize(rows: OrderBin[]) {
  let orders = 0, known = 0, late = 0, reviewed = 0, lateReviewed = 0, onTimeReviewed = 0, lateScores = 0, onTimeScores = 0;
  for (const row of rows) {
    orders += row.orders; reviewed += row.reviewed;
    if (row.delivery_status !== "unknown") known += row.orders;
    if (row.delivery_status === "late") { late += row.orders; lateReviewed += row.reviewed; lateScores += row.review_sum; }
    if (row.delivery_status === "on_time") { onTimeReviewed += row.reviewed; onTimeScores += row.review_sum; }
  }
  const lateReview = ratio(lateScores, lateReviewed), onTimeReview = ratio(onTimeScores, onTimeReviewed);
  return { orders, known, late, reviewed, lateReviewed, onTimeReviewed, lateRate: ratio(late, known), lateReview, onTimeReview,
    reviewGap: lateReview === null || onTimeReview === null ? null : lateReview - onTimeReview };
}

export function wilson(successes: number, total: number): [number, number] | null {
  if (!total) return null;
  const z = 1.959963984540054, p = successes / total, divisor = 1 + z * z / total;
  const center = (p + z * z / (2 * total)) / divisor;
  const width = z * Math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / divisor;
  return [Math.max(0, center - width), Math.min(1, center + width)];
}

export function cohortSummary(rows: CohortBin[], status: string) {
  const selected = rows.filter(row => row.first_delivery_status === status);
  const customers = selected.reduce((sum, row) => sum + row.customers, 0);
  const eligible = selected.reduce((sum, row) => sum + row.eligible_customers, 0);
  const repeated = selected.reduce((sum, row) => sum + row.repeat_customers, 0);
  return { customers, eligible, repeated, rate: ratio(repeated, eligible), interval: wilson(repeated, eligible) };
}

export function segmentRows(rows: OrderBin[], dimension: "customer_state" | "primary_category", minimum: number) {
  const groups = new Map<string, OrderBin[]>();
  for (const row of rows) {
    const group = groups.get(row[dimension]) || [];
    group.push(row); groups.set(row[dimension], group);
  }
  return [...groups].map(([name, values]) => ({ name, ...summarize(values) })).filter(row => row.known >= minimum).sort((a, b) => b.late - a.late || a.name.localeCompare(b.name));
}
