"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { cohortSummary, matches, segmentRows, summarize, type DeliveryData, type Filters } from "@/lib/delivery-metrics";
import "./delivery.css";

const number = (value: number) => new Intl.NumberFormat("en-US").format(value);
const percent = (value: number | null) => value === null ? "—" : `${(value * 100).toFixed(2)}%`;
const score = (value: number | null) => value === null ? "—" : value.toFixed(2);
const defaults: Filters = { from: "2016-09", to: "2018-08", state: "", category: "" };

export default function DeliveryPage() {
  const [data, setData] = useState<DeliveryData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [filters, setFilters] = useState(defaults);
  const [dimension, setDimension] = useState<"customer_state" | "primary_category">("customer_state");
  const [minimum, setMinimum] = useState(200);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/delivery-data.json", { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error("Analysis unavailable");
      return response.json();
    }).then(value => { setData(value); setError(false); }).catch(reason => { if (reason.name !== "AbortError") setError(true); });
    return () => controller.abort();
  }, [attempt]);
  const invalid = !filters.from || !filters.to || filters.from > filters.to;
  const rows = useMemo(() => data && !invalid ? data.orders.filter(row => matches(row, filters)) : [], [data, filters, invalid]);
  const cohorts = useMemo(() => data && !invalid ? data.cohorts.filter(row => matches(row, filters)) : [], [data, filters, invalid]);
  const summary = useMemo(() => summarize(rows), [rows]);
  const segments = useMemo(() => segmentRows(rows, dimension, minimum), [rows, dimension, minimum]);
  const lateCohort = cohortSummary(cohorts, "late"), onTimeCohort = cohortSummary(cohorts, "on_time");
  const ineligible = cohorts.reduce((sum, row) => sum + row.customers - row.eligible_customers, 0);
  const unknownCohort = cohorts.filter(row => row.first_delivery_status === "unknown").reduce((sum, row) => sum + row.eligible_customers, 0);
  const maxLate = Math.max(1, ...segments.map(row => row.late));
  function change(key: keyof Filters, value: string) { setFilters(current => ({ ...current, [key]: value })); }
  function exportCsv() {
    const content = [["Segment", "Delivered orders", "Known delivery dates", "Late orders", "Late rate", "Late review", "On-time review"], ...segments.map(row => [row.name, row.orders, row.known, row.late, row.lateRate ?? "", row.lateReview ?? "", row.onTimeReview ?? ""])];
    const csv = content.map(row => row.map(cell => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = `olist-${dimension}-${filters.from}-${filters.to}.csv`; link.click(); URL.revokeObjectURL(url);
  }
  return <main className="delivery-app">
    <a className="delivery-skip" href="#delivery-content">Skip to analysis</a>
    <header className="delivery-header"><Link className="delivery-brand" href="/"><span aria-hidden="true">O</span><strong>Olist <small>Commerce Pulse</small></strong></Link><nav aria-label="Reports"><Link href="/">Overview</Link><a href="/delivery" aria-current="page">Delivery &amp; retention</a></nav><span className="delivery-snapshot">Historical snapshot · 31 Aug 2018</span></header>
    <div className="delivery-body" id="delivery-content">
      <div className="delivery-title"><div><h1>Where are deliveries falling behind?</h1><p>Compare delivery delays, order reviews and a fixed 90-day repeat-purchase window.</p></div><button disabled={!segments.length} onClick={exportCsv}>Export segments ↓</button></div>
      <div className="delivery-filters" aria-label="Analysis filters">
        <label>From<input type="month" value={filters.from} min={data?.months[0]} max="2018-08" onChange={event => change("from", event.target.value)}/></label>
        <label>To<input type="month" value={filters.to} min={data?.months[0]} max="2018-08" onChange={event => change("to", event.target.value)}/></label>
        <label>Customer state<select value={filters.state} onChange={event => change("state", event.target.value)}><option value="">All states</option>{data?.states.map(state => <option key={state}>{state}</option>)}</select></label>
        <label>Primary category<select value={filters.category} onChange={event => change("category", event.target.value)}><option value="">All categories</option>{data?.categories.map(category => <option value={category} key={category}>{category.replaceAll("_", " ")}</option>)}</select></label>
        <button className="delivery-reset" onClick={() => setFilters(defaults)}>Reset filters</button>
      </div>
      {invalid && <p role="alert" className="delivery-message">Choose both months, with start on or before end.</p>}
      {!data && !error && <p role="status" className="delivery-message">Loading the saved Olist analysis…</p>}
      {error && <div role="alert" className="delivery-message">Could not load the saved analysis. <button onClick={() => { setError(false); setAttempt(value => value + 1); }}>Try again</button></div>}
      {data && <>
        <p className="delivery-scope" role="status">{number(summary.orders)} delivered orders in the selected purchase months. Delivered and reviewed outcomes are observed through {data.meta.asOf}. {number(summary.orders - summary.known)} orders have an unknown promised date.</p>
        <section className="delivery-kpis" aria-label="Selected delivery metrics">
          <div><span>Late delivery rate</span><strong>{percent(summary.lateRate)}</strong><small>{number(summary.late)} late / {number(summary.known)} with known dates</small></div>
          <div><span>Late-order review</span><strong>{score(summary.lateReview)}<em> / 5</em></strong><small>{number(summary.lateReviewed)} reviewed late orders</small></div>
          <div><span>On-time review</span><strong>{score(summary.onTimeReview)}<em> / 5</em></strong><small>{number(summary.onTimeReviewed)} reviewed on-time orders</small></div>
          <div><span>Review gap: late − on time</span><strong>{summary.reviewGap !== null && summary.reviewGap > 0 ? "+" : ""}{score(summary.reviewGap)}<em> points</em></strong><small>Descriptive association</small></div>
        </section>
        <div className="delivery-grid">
          <section className="delivery-panel"><div className="delivery-panel-title"><div><h2>Late orders by segment</h2><p>Ranked by late-order count, with the rate beside it.</p></div></div>
            <div className="delivery-segment-controls"><label>Group by<select value={dimension} onChange={event => setDimension(event.target.value as typeof dimension)}><option value="customer_state">Customer state</option><option value="primary_category">Primary category</option></select></label><label>Minimum orders with dates<select value={minimum} onChange={event => setMinimum(Number(event.target.value))}><option value={50}>50</option><option value={200}>200</option><option value={500}>500</option></select></label></div>
            {segments.length ? <ol className="delivery-bars">{segments.slice(0, 3).map(row => <li key={row.name}><div><span>{row.name.replaceAll("_", " ")}</span><strong>{number(row.late)} late <small>· {percent(row.lateRate)}</small></strong></div><div className="delivery-bar-track"><span style={{ width: `${row.late / maxLate * 100}%` }}/></div><small>{number(row.known)} orders with known delivery dates</small></li>)}</ol> : <p className="delivery-empty">No segments meet this sample threshold. Try a wider period or lower minimum.</p>}
            {segments.length > 0 && <a className="delivery-all-segments" href="#segment-detail">See all {segments.length} segments ↓</a>}
          </section>
          <section className="delivery-panel"><div className="delivery-panel-title"><div><h2>Did customers buy again?</h2><p>Another delivered order purchased within 90 days of the first purchase.</p></div></div>
            <div className="delivery-cohorts">{[{ name: "First order on time", group: onTimeCohort }, { name: "First order late", group: lateCohort }].map(({name, group}) => <div key={name}><h3>{name}</h3><strong>{percent(group.rate)}</strong><p>{number(group.repeated)} repeat / {number(group.eligible)} eligible customers</p><small>95% Wilson interval: {group.interval ? `${percent(group.interval[0])}–${percent(group.interval[1])}` : "—"}</small></div>)}</div>
            <p className="delivery-cohort-note">{number(ineligible)} newer customers excluded: a full 90-day window is not yet observed. {unknownCohort > 0 ? `${number(unknownCohort)} eligible customers have unknown first-delivery status.` : ""}</p>
            <p className="delivery-cohort-note">State, category and month filters describe the first delivered order in available history. A difference between groups does not show that delivery timing caused it.</p>
          </section>
        </div>
        <section id="segment-detail" className="delivery-panel delivery-table-panel"><div className="delivery-panel-title"><div><h2>Segment detail</h2><p>All qualifying segments. Each order belongs to one primary category.</p></div><span>{segments.length} segments</span></div>
          <div className="delivery-table-scroll"><table><caption className="delivery-sr">Delivery and review comparison for the selected segments</caption><thead><tr><th scope="col">{dimension === "customer_state" ? "State" : "Primary category"}</th><th scope="col">Orders</th><th scope="col">Late</th><th scope="col">Late rate</th><th scope="col">Late review / 5</th><th scope="col">On-time review / 5</th></tr></thead><tbody>{segments.map(row => <tr key={row.name}><th scope="row">{row.name.replaceAll("_", " ")}</th><td>{number(row.orders)}</td><td>{number(row.late)}</td><td>{percent(row.lateRate)}</td><td>{score(row.lateReview)}<small>n={number(row.lateReviewed)}</small></td><td>{score(row.onTimeReview)}<small>n={number(row.onTimeReviewed)}</small></td></tr>)}</tbody></table>{!segments.length && <p className="delivery-empty">No qualifying segments for these filters.</p>}</div>
        </section>
        <details className="delivery-method"><summary>Definitions and limitations</summary><p>Late means the actual delivery calendar date is after the estimated delivery calendar date; delivery later on the same day is on time. Reviews are averaged within each order before taking the order average. Missing reviews are excluded and their sample sizes are shown.</p><p>Primary category is the category with the largest summed product value in the order, with an alphabetical tie-break. This keeps each order, its payment value and review in one category.</p><p>Repeat purchase uses customer_unique_id and a strictly later purchase within 90 days. Both orders must have been delivered by the snapshot cutoff. Only first purchases with a complete follow-up window enter the denominator. Earlier purchases outside this dataset are unknown. Confidence intervals describe sampling variability; they do not remove confounding or selection bias.</p></details>
      </>}
      <footer className="delivery-footer">Olist public dataset · Analysis by Vũ Thanh Phong · <a href="https://github.com/Frey-Rayford/Olist-Ecommerce-Analytics" target="_blank" rel="noreferrer">Source &amp; methodology ↗</a></footer>
    </div>
  </main>;
}
