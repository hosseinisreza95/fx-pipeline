import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pipeline"))

from prefect import flow, task
from extract import extract_all
from transform import transform
from load import load
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "fx_dwh.sqlite")


@task(name="extract", retries=3, retry_delay_seconds=30)
def extract_task(start_date: str, end_date: str):
    """Fetch FX rates from frankfurter.app — retries 3 times on failure."""
    return extract_all(start_date, end_date)


@task(name="transform")
def transform_task(df, start_date: str, end_date: str):
    """Compute daily change, YTD, and year start rate."""
    return transform(df, start_date, end_date)


@task(name="load")
def load_task(df, db_path: str):
    """Load transformed data into SQLite DWH."""
    load(df, db_path)


@flow(name="fx-pipeline-daily")
def fx_pipeline_flow(mode: str = "daily", start: str = "", end: str = ""):

    if mode == "daily":
        start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = date.today().strftime("%Y-%m-%d")
    else:
        start_date = start
        end_date = end

    raw = extract_task(start_date, end_date)
    transformed = transform_task(raw, start_date, end_date)
    load_task(transformed, DB_PATH)


if __name__ == "__main__":
    fx_pipeline_flow(mode="daily")