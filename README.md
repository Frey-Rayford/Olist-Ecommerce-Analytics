# Olist E-commerce Analytics

[🇬🇧 English](README.md) · [🇻🇳 Tiếng Việt](README.vi.md)

An end-to-end Data Analyst portfolio project that converts the Brazilian Olist marketplace dataset into a reproducible Python pipeline, a validated SQL Server model, documented business analysis, and an interactive Next.js data story.

![Olist Commerce Pulse dashboard](assets/dashboard-preview.png)

## Project at a glance

| Scope | Result |
|---|---:|
| Source data | 9 CSV files · 1,550,922 rows |
| Delivered orders analyzed | 96,478 |
| Delivered GMV | R$15.42M |
| Comparable Jan–Aug GMV growth | +143.3% YoY |
| Late-delivery rate | 8.11% |
| Review-score gap for late orders | −1.73 points |

> **Metric definition:** Delivered GMV is the sum of customer payment value for delivered orders and includes freight. Product value is reported separately and excludes freight.

## Business questions

1. How did delivered GMV and order volume change over time?
2. Which product categories and customer states generated the most value?
3. How was delivery performance associated with review scores?
4. Which operational segments deserve deeper investigation?
5. What does the low repeat-customer rate suggest for retention analysis?

## What I built

- A reusable Python cleaning pipeline for nine related CSV files.
- Automated checks for row counts, primary keys, composite keys, foreign keys, ZIP-code formatting, and calculated fields.
- A SQL Server 2019 staging and core model with constraints, indexes, reusable views, KPI queries, and data-quality checks.
- An executed Jupyter Notebook for exploratory analysis and portfolio charts.
- A Next.js dashboard that imports a generated `analytics.json` file instead of hardcoded KPI values.
- Reproducible setup scripts and documentation for local execution.

## Data pipeline

![Olist analytics pipeline](assets/pipeline-overview.svg)

```text
Raw CSV files
    ↓
Python cleaning and validation
    ↓
Processed analytical CSV files
    ├── SQL Server staging → core model → KPI validation
    └── Generated dashboard/data/analytics.json
                              ↓
                         Next.js dashboard
```

## Key findings

- Delivered GMV reached **R$15.42M** across **96,478** delivered orders.
- Jan–Aug 2018 delivered GMV was **143.3%** above the comparable 2017 period.
- **8.11%** of delivered orders arrived after the estimated delivery date.
- Late orders averaged **2.57/5** in reviews versus **4.29/5** for on-time or early orders.
- SP, RJ, and MG generated approximately **62.5%** of delivered GMV.
- The repeat-customer rate was approximately **3.0%**.
- Customers whose first delivered order was late repeated at **2.52%**, compared with **3.04%** for customers whose first order arrived on time or early. This is a descriptive association, not a causal estimate.

## Selected analysis

<table>
  <tr>
    <td width="50%"><img src="assets/monthly_gmv.png" alt="Monthly delivered GMV trend"></td>
    <td width="50%"><img src="assets/delivery_review.png" alt="Review score by delivery status"></td>
  </tr>
  <tr>
    <td align="center"><strong>Commercial momentum</strong></td>
    <td align="center"><strong>Delivery and customer satisfaction</strong></td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%"><img src="assets/top_categories_product_value.png" alt="Top product categories by product value"></td>
    <td width="50%"><img src="assets/top_states_gmv.png" alt="Top customer states by delivered GMV"></td>
  </tr>
  <tr>
    <td align="center"><strong>Product portfolio</strong></td>
    <td align="center"><strong>Geographic concentration</strong></td>
  </tr>
</table>

<table>
  <tr>
    <td width="100%"><img src="assets/first_order_delivery_retention.png" alt="Repeat-purchase rate by first-order delivery status"></td>
  </tr>
  <tr>
    <td align="center"><strong>Retention by first-order delivery experience</strong></td>
  </tr>
</table>

## Repository structure

```text
assets/          Dashboard preview, diagrams, and analysis charts
data/
  raw/           Original source files, excluded from Git
  processed/     Generated analytical files, excluded from Git
  sample/        Documentation for lightweight examples
notebooks/       Executed exploratory analysis notebook
reports/         Data model, inventory, processing, and KPI documentation
sql/             SQL Server schema, transformations, views, KPIs, and checks
src/             Python processing, validation, and dashboard export scripts
dashboard/       Next.js, React, TypeScript, and generated analytics JSON
```

## Run locally

### 1. Get the dataset

Download the **Brazilian E-Commerce Public Dataset by Olist** from Kaggle and place the nine original CSV files in `data/raw/`. The exact filenames are listed in [`data/README.md`](data/README.md).

The downloadable local package of this project already includes the source data. The files remain excluded by `.gitignore`, so they are not pushed to GitHub when using Git normally.

### 2. Build and validate the analytical data

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
python src/run_pipeline.py
```

A successful run ends with:

```text
CHECKS_OK|files=9|orders=99441|items=112650
DASHBOARD_DATA_OK|dashboard/data/analytics.json
PIPELINE_OK
```

### 3. Run the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open `http://localhost:3000`.

### 4. Build the production dashboard

```bash
cd dashboard
npm run lint
npm run build
```

## Continuous integration

`.github/workflows/quality.yml` runs the same checks on every push: compile the Python source, validate `dashboard/data/analytics.json`, run a small-data cleaning and KPI regression suite, then lint, type-check, and build the dashboard.

## SQL Server workflow

Follow [`sql/README.md`](sql/README.md), then execute the scripts in this order:

1. `00_create_database.sql`
2. `01_create_tables.sql`
3. `02_bulk_load_staging.sql`
4. `03_transform_to_core.sql`
5. `04_create_views.sql`
6. `06_data_quality_checks.sql`
7. `05_kpi_analysis.sql`

## Documentation

- [Data model](reports/data_model.md)
- [Raw data inventory](reports/raw_data_inventory.md)
- [Processing notes](reports/processing_notes.md)
- [SQL KPI results](reports/sql_kpi_results.md)
- [Executed EDA notebook](notebooks/01_olist_eda.ipynb)
- [Dashboard documentation](dashboard/README.md)

## Limitations

- The analysis is observational and does not establish that late delivery causes lower reviews or lower repeat behavior.
- The dataset ends in 2018 and does not represent current Olist performance.
- Customer identity is pseudonymized and demographic attributes are unavailable.
- Carrier-level data is not included, so logistics recommendations require further operational data.
- Raw data is excluded from GitHub because of repository size and must be downloaded separately.

## Tech stack

`Python` · `Pandas` · `Jupyter` · `SQL Server 2019` · `T-SQL` · `Next.js` · `React` · `TypeScript` · `CSS`

## License

Project code is available under the [MIT License](LICENSE). The Olist dataset remains subject to its original source terms.

## Pipeline tests

`python -m unittest discover -s tests -v` runs without downloading the full dataset or starting SQL Server. The fixture exercises cleaning, key checks and dashboard export. Tests also verify that duplicate item keys and unknown orders are rejected, and that order-level GMV is not multiplied by joins. Full-dataset row-count checks remain in `src/validate_processed_data.py`.
