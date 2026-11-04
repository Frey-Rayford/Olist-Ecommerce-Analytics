"use client";

import { useMemo, useState } from "react";
import analytics from "@/data/analytics.json";

type Metric = "gmv" | "orders";

type StateNameMap = Record<string, string>;

const stateNames: StateNameMap = {
  SP: "São Paulo",
  RJ: "Rio de Janeiro",
  MG: "Minas Gerais",
  RS: "Rio Grande do Sul",
  PR: "Paraná",
};

const formatNumber = (value: number) =>
  new Intl.NumberFormat("en-US").format(value);

const formatCurrency = (value: number, digits = 2) =>
  `R$${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)}`;

const formatCompact = (value: number, metric: Metric) => {
  if (metric === "orders") return formatNumber(value);
  return `R$${(value / 1_000_000).toFixed(2)}M`;
};

export default function Home() {
  const [metric, setMetric] = useState<Metric>("gmv");
  const maxValue = useMemo(
    () => Math.max(...analytics.monthly.map((item) => item[metric])),
    [metric],
  );

  const creditCard = analytics.paymentMix.find(
    (payment) => payment.type === "credit_card",
  );
  const boleto = analytics.paymentMix.find((payment) => payment.type === "boleto");
  const otherPaymentShare = analytics.paymentMix
    .filter((payment) => !["credit_card", "boleto"].includes(payment.type))
    .reduce((sum, payment) => sum + payment.sharePct, 0);
  const topThreeStateShare = analytics.states
    .slice(0, 3)
    .reduce((sum, state) => sum + state.sharePct, 0);

  return (
    <main>
      <header className="siteHeader">
        <a className="brand" href="#overview" aria-label="Olist Commerce Pulse home">
          <span className="brandMark">O</span>
          <span>
            <strong>OLIST</strong>
            <small>COMMERCE PULSE</small>
          </span>
        </a>
        <nav aria-label="Dashboard sections">
          <a href="#growth">Growth</a>
          <a href="#market">Market</a>
          <a href="#operations">Operations</a>
          <a href="/delivery">Delivery &amp; retention</a>
          <a href="#methodology">Method</a>
        </nav>
        <div className="dataBadge">
          <span /> Data through {analytics.meta.dataThrough}
        </div>
      </header>

      <section className="hero" id="overview">
        <div className="heroCopy">
          <p className="eyebrow">Brazilian e-commerce · Analytical data story</p>
          <h1>Sales, delivery<br />and repeat orders.</h1>
          <p className="heroLead">
            Explore sales, delivery timing and customer reviews in the Olist
            public dataset. Open the delivery report to filter segments and compare repeat purchases.
          </p>
          <div className="heroTags" aria-label="Project technology stack">
            <span>Python pipeline</span>
            <span>SQL Server model</span>
            <span>Next.js dashboard</span>
          </div>
        </div>
        <aside className="heroInsight">
          <p>Primary finding</p>
          <strong>−{analytics.delivery.reviewGap.toFixed(2)}</strong>
          <span>review points for late orders versus on-time orders</span>
        </aside>
      </section>

      <section className="foundationStrip" aria-label="Data foundation summary">
        <div><strong>{analytics.meta.sourceFiles}</strong><span>source files</span></div>
        <div><strong>{(analytics.meta.sourceRows / 1_000_000).toFixed(2)}M</strong><span>raw records profiled</span></div>
        <div><strong>{formatNumber(analytics.meta.deliveredOrderRows)}</strong><span>delivered orders analyzed</span></div>
        <div><strong>PK · FK · totals</strong><span>automated validation</span></div>
      </section>

      <section className="kpiGrid" aria-label="Executive KPIs">
        <article className="kpiCard featured">
          <p>Delivered GMV</p>
          <strong>{formatCompact(analytics.kpis.deliveredGmv, "gmv")}</strong>
          <span className="positive">↗ {analytics.kpis.yoyGmvGrowth}% Jan–Aug YoY</span>
        </article>
        <article className="kpiCard">
          <p>Delivered orders</p>
          <strong>{formatNumber(analytics.kpis.deliveredOrders)}</strong>
          <span>{formatNumber(analytics.kpis.uniqueCustomers)} unique customers</span>
        </article>
        <article className="kpiCard">
          <p>Average order value</p>
          <strong>{formatCurrency(analytics.kpis.averageOrderValue)}</strong>
          <span>Payment value including freight</span>
        </article>
        <article className="kpiCard alert">
          <p>Late delivery rate</p>
          <strong>{analytics.kpis.lateDeliveryRate}%</strong>
          <span>{formatNumber(analytics.kpis.lateOrders)} late / {formatNumber(analytics.kpis.knownDeliveryDateOrders)} with known dates</span>
        </article>
        <article className="kpiCard">
          <p>Average review</p>
          <strong>{analytics.kpis.averageReviewScore} / 5</strong>
          <span>{analytics.kpis.positiveReviewShare}% are 4–5 stars</span>
        </article>
      </section>

      <section className="dashboardGrid" id="growth">
        <article className="panel trendPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Growth signal</p>
              <h2>Monthly commercial momentum</h2>
            </div>
            <div className="metricToggle" role="group" aria-label="Chart metric">
              <button
                className={metric === "gmv" ? "active" : ""}
                onClick={() => setMetric("gmv")}
                type="button"
              >
                GMV
              </button>
              <button
                className={metric === "orders" ? "active" : ""}
                onClick={() => setMetric("orders")}
                type="button"
              >
                Orders
              </button>
            </div>
          </div>
          <div className="barChart" aria-label={`Monthly ${metric} chart`}>
            {analytics.monthly.map((item, index) => {
              const value = item[metric];
              const height = `${Math.max(7, (value / maxValue) * 100)}%`;
              const showLabel = index % 3 === 0 || index === analytics.monthly.length - 1;
              return (
                <div className="monthColumn" key={item.month}>
                  <span className="barValue">{formatCompact(value, metric)}</span>
                  <div
                    className="monthBar"
                    style={{ height }}
                    title={`${item.month}: ${formatCompact(value, metric)}`}
                  />
                  <span className="monthLabel">{showLabel ? item.month : ""}</span>
                </div>
              );
            })}
          </div>
          <div className="chartNote">
            <strong>{formatCompact(analytics.kpis.comparableGmv2018, "gmv")}</strong>
            <span>
              Jan–Aug 2018 delivered GMV, up from {formatCompact(analytics.kpis.comparableGmv2017, "gmv")} in 2017
            </span>
          </div>
        </article>

        <article className="panel paymentPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Payment behavior</p>
              <h2>Credit-led checkout</h2>
            </div>
          </div>
          <div className="paymentBody">
            <div
              className="donut"
              style={{ "--credit-share": `${creditCard?.sharePct ?? 0}%`, "--boleto-end": `${(creditCard?.sharePct ?? 0) + (boleto?.sharePct ?? 0)}%` } as React.CSSProperties}
              aria-label={`Credit-card share ${creditCard?.sharePct ?? 0} percent`}
            >
              <div><strong>{creditCard?.sharePct ?? 0}%</strong><span>credit card</span></div>
            </div>
            <ul className="legend">
              <li><i className="credit" />Credit card <strong>{creditCard?.sharePct ?? 0}%</strong></li>
              <li><i className="boleto" />Boleto <strong>{boleto?.sharePct ?? 0}%</strong></li>
              <li><i className="other" />Voucher + debit <strong>{otherPaymentShare.toFixed(1)}%</strong></li>
            </ul>
          </div>
          <p className="panelFootnote">
            Average credit-card installment count: {creditCard?.averageInstallments ?? 0}
          </p>
        </article>
      </section>

      <section className="dashboardGrid marketGrid" id="market">
        <article className="panel categoryPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Product portfolio</p>
              <h2>Top categories by product value</h2>
            </div>
            <span className="unitLabel">Delivered orders only</span>
          </div>
          <div className="rankList">
            {analytics.categories.map((category, index) => (
              <div className="rankRow" key={category.name}>
                <span className="rankNumber">{String(index + 1).padStart(2, "0")}</span>
                <div className="rankContent">
                  <div>
                    <strong>{category.name}</strong>
                    <span>{formatCompact(category.productValue, "gmv")}</span>
                  </div>
                  <div className="track">
                    <i style={{ width: `${(category.productValue / analytics.categories[0].productValue) * 100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel statePanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Geographic concentration</p>
              <h2>Top customer states</h2>
            </div>
          </div>
          <div className="stateList">
            {analytics.states.map((state) => (
              <div className="stateRow" key={state.code}>
                <span className="stateCode">{state.code}</span>
                <div>
                  <strong>{stateNames[state.code] ?? state.code}</strong>
                  <small>{formatCompact(state.gmv, "gmv")}</small>
                </div>
                <span>{state.sharePct}%</span>
              </div>
            ))}
          </div>
          <div className="concentrationCallout">
            <strong>{topThreeStateShare.toFixed(1)}%</strong>
            <span>of delivered GMV comes from SP, RJ and MG</span>
          </div>
        </article>
      </section>

      <section className="operationsSection" id="operations">
        <div className="sectionIntro">
          <p className="sectionLabel">Operational opportunity</p>
          <h2>Late delivery is associated with weaker reviews</h2>
          <p>
            Late orders take nearly three times longer and receive materially
            lower review scores. This cohort is a strong candidate for deeper
            carrier, seller, and category diagnostics.
          </p>
          <div className="priorityStates" aria-label="Highest late-delivery-rate states">
            {analytics.delivery.priorityStates.map((state) => (
              <span key={state.code}>
                <strong>{state.code}</strong> {state.lateDeliveryRate}% late
              </span>
            ))}
          </div>
        </div>
        <div className="deliveryCompare">
          <article className="deliveryCard onTime">
            <p>On time or early</p>
            <strong>{analytics.delivery.onTimeOrEarly.averageReviewScore}</strong>
            <span>average review score</span>
            <div className="scoreTrack"><i style={{ width: `${analytics.delivery.onTimeOrEarly.averageReviewScore / 5 * 100}%` }} /></div>
            <dl>
              <div><dt>Orders</dt><dd>{formatNumber(analytics.delivery.onTimeOrEarly.orders)}</dd></div>
              <div><dt>Delivery</dt><dd>{analytics.delivery.onTimeOrEarly.averageDeliveryDays} days</dd></div>
            </dl>
          </article>
          <article className="deliveryCard late">
            <p>Late delivery</p>
            <strong>{analytics.delivery.late.averageReviewScore}</strong>
            <span>average review score</span>
            <div className="scoreTrack"><i style={{ width: `${analytics.delivery.late.averageReviewScore / 5 * 100}%` }} /></div>
            <dl>
              <div><dt>Orders</dt><dd>{formatNumber(analytics.delivery.late.orders)}</dd></div>
              <div><dt>Delivery</dt><dd>{analytics.delivery.late.averageDeliveryDays} days</dd></div>
            </dl>
          </article>
        </div>
      </section>

      <section className="recommendation">
        <div className="recommendationIndex">01</div>
        <div>
          <p className="sectionLabel">Recommended next move</p>
          <h2>Prioritize late-order prevention in AL, MA, PI and CE.</h2>
          <p>
            Combine carrier, seller and category diagnostics with proactive
            customer communication. Track late-delivery rate and review-score recovery weekly.
          </p>
        </div>
        <div className="retentionStat">
          <strong>{analytics.retention.overallRepeatRate}%</strong>
          <span>overall repeat-customer rate</span>
          <small>
            Observed across the available history, without a fixed follow-up window. Open the delivery report for the 90-day cohort comparison.
          </small>
        </div>
      </section>

      <section className="methodologySection" id="methodology">
        <div className="methodologyHeading">
          <p className="sectionLabel">Data foundation</p>
          <h2>Numbers are generated, not typed into the UI.</h2>
          <p>
            The dashboard imports a version-controlled JSON artifact produced by
            the Python pipeline. SQL Server independently validates row counts,
            relationships, calculated fields, and business KPIs.
          </p>
        </div>
        <div className="pipelineFlow" aria-label="Project data flow">
          <div><span>01</span><strong>Raw CSV</strong><small>{analytics.meta.sourceFiles} source files</small></div>
          <b>→</b>
          <div><span>02</span><strong>Python</strong><small>clean + validate</small></div>
          <b>→</b>
          <div><span>03</span><strong>SQL Server</strong><small>model + KPI checks</small></div>
          <b>→</b>
          <div><span>04</span><strong>JSON</strong><small>dashboard contract</small></div>
          <b>→</b>
          <div><span>05</span><strong>Next.js</strong><small>interactive story</small></div>
        </div>
        <div className="metricNotes">
          <p><strong>Delivered GMV</strong><span>Sum of payment value for delivered orders, including freight.</span></p>
          <p><strong>Product value</strong><span>Sum of item prices for delivered orders, excluding freight.</span></p>
          <p><strong>Association note</strong><span>Delivery and retention findings are descriptive, not causal claims.</span></p>
        </div>
      </section>

      <footer>
        <div>
          <strong>Olist Commerce Pulse</strong>
          <span>End-to-end analytics portfolio project</span>
        </div>
        <p>SQL Server 2019 · Python · Next.js · {formatNumber(analytics.kpis.deliveredOrders)} delivered orders</p>
      </footer>
    </main>
  );
}
