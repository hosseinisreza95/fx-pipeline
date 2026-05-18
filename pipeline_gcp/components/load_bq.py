from google.cloud import bigquery
import pandas as pd

# =============================================
# FX Pipeline GCP - Load to BigQuery
# =============================================

PROJECT_ID = "fx-pipeline-496417"
DATASET_ID = "fx_dwh"
TABLE_ID = "fact_fx_rates"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


def load_to_bigquery(df: pd.DataFrame) -> None:
    """
    Loads transformed DataFrame into BigQuery.
    Creates table if it doesn't exist.
    Deletes existing rows for the same dates before inserting (idempotent).
    """

    client = bigquery.Client(project=PROJECT_ID)

    # define schema
    schema = [
        bigquery.SchemaField("pair_label",       "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("base",             "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("quote",            "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("date",             "DATE",      mode="REQUIRED"),
        bigquery.SchemaField("rate",             "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("prev_day_rate",    "FLOAT64",   mode="NULLABLE"),
        bigquery.SchemaField("daily_change_pct", "FLOAT64",   mode="NULLABLE"),
        bigquery.SchemaField("year_start_rate",  "FLOAT64",   mode="NULLABLE"),
        bigquery.SchemaField("ytd_pct",          "FLOAT64",   mode="NULLABLE"),
        bigquery.SchemaField("ingested_at",      "TIMESTAMP", mode="REQUIRED"),
    ]

    # prepare dataframe
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["ingested_at"] = pd.Timestamp.utcnow()
    df["pair_label"] = df["base"] + "/" + df["quote"]

    # keep only schema columns
    columns = [field.name for field in schema]
    df = df[columns]

    # delete existing rows for the same dates before inserting (idempotency)
    dates = [str(d) for d in df["date"].unique().tolist()]
    dates_str = ", ".join([f"'{d}'" for d in dates])
    delete_query = f"DELETE FROM `{FULL_TABLE_ID}` WHERE date IN ({dates_str})"
    client.query(delete_query).result()
    print(f"Deleted existing rows for dates: {dates}")

    # load config
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )

    job = client.load_table_from_dataframe(df, FULL_TABLE_ID, job_config=job_config)
    job.result()

    table = client.get_table(FULL_TABLE_ID)
    print(f"Loaded {len(df)} rows. Total in BigQuery: {table.num_rows}")