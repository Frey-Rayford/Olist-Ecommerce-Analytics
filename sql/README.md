# Run the SQL Server model

The scripts target SQL Server 2019 and build a dedicated database named `olist_analytics`.

## Connect

Connect through SQL Server Management Studio or the SQL Server extension for VS Code using your local instance, for example:

```text
localhost
localhost\<INSTANCE_NAME>
```

Use Windows Authentication or another account with permission to create a database and run `BULK INSERT`.

## Execution order

Run each file in full:

1. `00_create_database.sql`
2. `01_create_tables.sql`
3. `02_bulk_load_staging.sql`
4. `03_transform_to_core.sql`
5. `04_create_views.sql`
6. `06_data_quality_checks.sql`
7. `05_kpi_analysis.sql`

After step 6:

- All expected row-count checks should return `PASS`.
- Duplicate primary or composite keys should return `0`.
- Orphaned foreign keys should return `0` for required relationships.
- Calculated-value checks should return `0` failures.

## Configure the processed-data path

Before running `02_bulk_load_staging.sql`, replace the example root path with the absolute path to your local `data\processed` directory:

```text
<PROJECT_PATH>\data\processed
```

## If `BULK INSERT` returns Access denied

`BULK INSERT` is executed by the SQL Server service account. Grant that account read access to the local `data\processed` directory, then rerun `02_bulk_load_staging.sql`.

## Safe reruns

- `02_bulk_load_staging.sql` truncates and reloads staging tables.
- `03_transform_to_core.sql` replaces data only inside the `olist_analytics` database.
- The scripts do not delete other databases.
