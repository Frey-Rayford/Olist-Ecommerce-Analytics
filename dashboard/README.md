# Olist Commerce Pulse Dashboard

An interactive analytical data story built with Next.js, React, TypeScript, and CSS.

## Data contract

The interface imports `data/analytics.json`. That file is generated from the processed CSV files by:

```powershell
python ../src/export_dashboard_data.py
```

KPI values are therefore produced by the analysis pipeline rather than typed into the React component.

## Run locally

```powershell
npm install
npm run dev
```

Open `http://localhost:3000`.

## Validate a production build

```powershell
npm run lint
npm run build
```

## Main sections

- Executive KPI summary
- Monthly delivered GMV and order trends
- Payment-method mix
- Product and geographic concentration
- Delivery performance and review association
- Retention context and operational recommendations
- Metric definitions and project data flow
