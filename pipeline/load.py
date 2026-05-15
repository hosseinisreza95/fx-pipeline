import sqlite3
import pandas as pd
from datetime import datetime, timezone

# =============================================
# FX Pipeline - Load
# Loads transformed data into SQLite DWH
# =============================================


def get_pair_id_map(conn: sqlite3.Connection) -> dict:
    """
    Returns a dictionary mapping pair_label to pair_id.
    e.g. {"EUR/NOK": 1, "EUR/SEK": 2, ...}
    """
    rows = conn.execute("SELECT id, pair_label FROM dim_currency_pair").fetchall()
    return {label: id for id, label in rows}


def load(df: pd.DataFrame, db_path: str) -> None:
    """
    Loads transformed DataFrame into fact_fx_rates table.
    Uses INSERT OR IGNORE for idempotency — safe to run multiple times.
    """

    conn = sqlite3.connect(db_path)
    pair_id_map = get_pair_id_map(conn)
    ingested_at = datetime.now(timezone.utc).isoformat()

    rows_to_insert = []

    for _, row in df.iterrows():
        pair_label = f"{row['base']}/{row['quote']}"
        pair_id = pair_id_map.get(pair_label)

        if pair_id is None:
            print(f"Warning: pair {pair_label} not found in dim_currency_pair, skipping.")
            continue

        rows_to_insert.append((
            pair_id,
            row["date"].strftime("%Y-%m-%d"),
            row["rate"],
            row["prev_day_rate"] if pd.notna(row["prev_day_rate"]) else None,
            row["daily_change_pct"] if pd.notna(row["daily_change_pct"]) else None,
            row["year_start_rate"] if pd.notna(row["year_start_rate"]) else None,
            row["ytd_pct"] if pd.notna(row["ytd_pct"]) else None,
            ingested_at
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO fact_fx_rates 
            (pair_id, date, rate, prev_day_rate, daily_change_pct, year_start_rate, ytd_pct, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)

    conn.commit()

    loaded = conn.execute("SELECT COUNT(*) FROM fact_fx_rates").fetchone()[0]
    print(f"Inserted {len(rows_to_insert)} rows. Total in DB: {loaded}")

    conn.close()


# -----------------------------------------------
# Quick test
# -----------------------------------------------
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))

    from extract import extract_all
    from transform import transform

    DB_PATH = r"C:\Users\hosse\Desktop\fx-pipeline\db\fx_dwh.sqlite"

    raw = extract_all("2024-01-01", "2024-12-31")
    transformed = transform(raw, "2024-01-01", "2024-12-31")
    load(transformed, DB_PATH)