import sqlite3
import os
from itertools import permutations

# =============================================
# FX Pipeline - Database Initializer
# Creates tables and seeds dimension data
# Run once before pipeline
# =============================================

# works both locally and inside Docker
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fx_dwh.sqlite")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # create tables from schema
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())

    # seed dim_currency_pair with all 42 cross-pairs
    currencies = ['EUR', 'NOK', 'SEK', 'PLN', 'RON', 'DKK', 'CZK']
    pairs = [(a, b, f"{a}/{b}") for a, b in permutations(currencies, 2)]

    conn.executemany("""
        INSERT OR IGNORE INTO dim_currency_pair (base, quote, pair_label)
        VALUES (?, ?, ?)
    """, pairs)

    conn.commit()

    pair_count = conn.execute("SELECT COUNT(*) FROM dim_currency_pair").fetchone()[0]
    print(f"Tables created successfully.")
    print(f"Currency pairs seeded: {pair_count}")

    conn.close()


if __name__ == "__main__":
    init_db()