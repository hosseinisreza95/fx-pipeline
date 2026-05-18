import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import date, timedelta
import argparse

from components.extract import extract_all
from components.transform import transform
from components.load_bq import load_to_bigquery

# =============================================
# FX Pipeline GCP - Entry Point
# =============================================


def run(mode: str, start: str = "", end: str = ""):

    if mode == "daily":
        end_date = date.today().strftime("%Y-%m-%d")
        start_date = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
    else:
        start_date = start
        end_date = end

    print("=" * 40)
    print(f"FX Pipeline GCP (mode: {mode})")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 40)

    print("\n[1/3] Extracting...")
    raw = extract_all(start_date, end_date)

    print("\n[2/3] Transforming...")
    transformed = transform(raw, start_date, end_date)

    print("\n[3/3] Loading to BigQuery...")
    load_to_bigquery(transformed)

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daily", "historical"], default="daily")
    parser.add_argument("--start", type=str, default="")
    parser.add_argument("--end", type=str, default="")
    args = parser.parse_args()
    run(args.mode, args.start, args.end)