import sys
import os
import argparse
from datetime import date, timedelta

sys.path.append(os.path.dirname(__file__))

from extract import extract_all
from transform import transform
from load import load

# =============================================
# FX Pipeline - Entry Point
# 
# Two modes:
# 1. historical: loads a custom date range (first time setup)
# 2. daily: loads yesterday's data (scheduled run)
#
# Usage:
#   Historical: python run_pipeline.py --mode historical --start 2024-01-01 --end 2024-12-31
#   Daily:      python run_pipeline.py --mode daily
# =============================================

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "fx_dwh.sqlite")


def get_dates(mode: str, start: str = None, end: str = None):
    """
    Returns (start_date, end_date) based on mode.
    - historical: uses provided start/end
    - daily: yesterday to today
    """
    if mode == "daily":
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = date.today().strftime("%Y-%m-%d")
        return yesterday, today

    elif mode == "historical":
        if not start or not end:
            raise ValueError("historical mode requires --start and --end arguments.")
        return start, end

    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'daily' or 'historical'.")


def run(mode: str, start: str = None, end: str = None):
    start_date, end_date = get_dates(mode, start, end)

    print("=" * 40)
    print(f"FX Pipeline Starting... (mode: {mode})")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 40)

    print("\n[1/3] Extracting...")
    raw = extract_all(start_date, end_date)

    print("\n[2/3] Transforming...")
    transformed = transform(raw, start_date, end_date)

    print("\n[3/3] Loading...")
    load(transformed, DB_PATH)

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FX Pipeline Runner")
    parser.add_argument("--mode", choices=["daily", "historical"], default="daily")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD) for historical mode")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD) for historical mode")

    args = parser.parse_args()
    run(args.mode, args.start, args.end)