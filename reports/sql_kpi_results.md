# SQL KPI validation

The previous recorded SQL run used the old timestamp definition of late delivery. Its delivery and retention group results are superseded.

Rebuild processed files with `python src/run_pipeline.py`, reload staging and core, then run `sql/06_data_quality_checks.sql`, `sql/05_kpi_analysis.sql` and `sql/07_delivery_retention.sql` in SQL Server. The new delivery SQL has not been executed against SQL Server as part of this update.

Current Python results and exact denominators are in `delivery_findings.json`; definitions and snapshot scope are in `delivery_case_study.md`. Do not compare its snapshot counts with a final-dataset SQL query without applying the same cutoff.
