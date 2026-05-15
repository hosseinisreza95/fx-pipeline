# FX Pipeline

A daily foreign-exchange (FX) rate ingestion pipeline that fetches rates
for 7 currencies, computes YTD and daily change metrics, and loads them
into a SQLite data warehouse.

---

## Project Structure

```
fx-pipeline/
├── README.md
├── requirements.txt
├── design_notes.md
├── Dockerfile
├── docker-compose.yml
├── pipeline/
│   ├── extract.py          # Fetch FX rates from frankfurter.app
│   ├── transform.py        # Compute YTD, daily change, year start rate
│   ├── load.py             # Load into SQLite DWH
│   └── run_pipeline.py     # Entry point
├── db/
│   ├── schema.sql          # DDL
│   ├── init_db.py          # Creates tables and seeds dimension data
│   └── fx_dwh.sqlite       # SQLite database (created on first run)
├── queries/
│   └── example_queries.sql # Example SQL queries
└── orchestration/
    ├── prefect_flow.py     # Local scheduling with Prefect
    └── azure_proposal.md   # Azure deployment proposal
```

---

## Option A: Run with Docker (recommended)

### 1. Build image

```bash
docker build -t fx-pipeline .
```

### 2. Historical load (first time)

```bash
docker run -v ${PWD}/db:/app/db fx-pipeline \
  python pipeline/run_pipeline.py --mode historical \
  --start 2024-01-01 --end 2024-12-31
```

### 3. Daily load

```bash
docker run -v ${PWD}/db:/app/db fx-pipeline
```

---

## Option B: Run locally (without Docker)

### 1. Create virtual environment

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize database

```bash
python db/init_db.py
```

### 4. Run pipeline

```bash
# historical load
python pipeline/run_pipeline.py --mode historical --start 2024-01-01 --end 2024-12-31

# daily load
python pipeline/run_pipeline.py --mode daily
```

---

## Validating Output

Open `db/fx_dwh.sqlite` with [DB Browser for SQLite](https://sqlitebrowser.org/)
or run the example queries:

```bash
# check row counts
sqlite3 db/fx_dwh.sqlite "SELECT COUNT(*) FROM fact_fx_rates;"

# check no duplicates
sqlite3 db/fx_dwh.sqlite "
SELECT pair_id, date, COUNT(*)
FROM fact_fx_rates
GROUP BY pair_id, date
HAVING COUNT(*) > 1;"
```

See `queries/example_queries.sql` for more examples including
YTD calculations and daily change lookups.

---

## Currencies

| Code | Name |
|------|------|
| EUR | Euro |
| NOK | Norwegian Krone |
| SEK | Swedish Krona |
| PLN | Polish Zloty |
| RON | Romanian Leu |
| DKK | Danish Krone |
| CZK | Czech Koruna |

7 currencies × 6 counterparts = **42 cross-pairs** per trading day.

---

## YTD Definition

YTD (Year-To-Date) is defined as the percentage change from the
first available trading day of the year to the current date:

```
YTD % = (rate_today - rate_year_start) / year_start_rate × 100
```

Both YTD and daily change are pre-computed at load time and stored
in the fact table for query simplicity.

---

## Orchestration

See `orchestration/azure_proposal.md` for the Azure deployment proposal
using Azure Data Factory with a daily 6:00 AM UTC trigger.

For local scheduling, see `orchestration/prefect_flow.py`.

---

## Design Decisions

See `design_notes.md` for key decisions and trade-offs.