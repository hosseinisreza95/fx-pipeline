# FX Pipeline

A daily foreign-exchange (FX) rate ingestion pipeline that fetches rates
for 7 currencies, computes YTD and daily change metrics, and loads them
into a data warehouse.

---

## Architecture
frankfurter.app API
↓
Python ETL Pipeline
↓
┌───────────────────┬────────────────────┐
│   Local / SQLite  │   GCP / BigQuery   │
│   (pipeline/)     │   (pipeline_gcp/)  │
└───────────────────┴────────────────────┘
↓                    ↓
Docker + Prefect    Cloud Run + Scheduler
↓
Looker Studio Dashboard

---

## Project Structure
fx-pipeline/
├── pipeline/                # SQLite version (local)
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── run_pipeline.py
├── pipeline_gcp/            # GCP version (production)
│   ├── components/
│   │   ├── extract.py
│   │   ├── transform.py
│   │   └── load_bq.py       # loads to BigQuery
│   └── main.py
├── db/
│   ├── schema.sql
│   ├── init_db.py
│   └── fx_dwh.sqlite
├── queries/
│   └── example_queries.sql
├── orchestration/
│   ├── prefect_flow.py
│   └── azure_proposal.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── design_notes.md

---

## Option A: GCP Version (production)

### Prerequisites
- Google Cloud account
- `gcloud` CLI installed and authenticated
- BigQuery dataset created

### 1. Authenticate
```bash
gcloud auth application-default login
```

### 2. Historical load (first time)
```bash
python pipeline_gcp/main.py --mode historical --start 2024-01-01 --end 2024-12-31
```

### 3. Daily load
```bash
python pipeline_gcp/main.py --mode daily
```

### 4. Dashboard
Live dashboard available on Looker Studio — connected directly to BigQuery.

---

## Option B: Local Version (SQLite + Docker)

### 1. Build Docker image
```bash
docker build -t fx-pipeline .
```

### 2. Historical load
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

YTD is defined as percentage change from the first available trading
day of the year to the current date:
YTD % = (rate_today - rate_year_start) / rate_year_start × 100

---

## Design Decisions

See `design_notes.md` for key decisions and trade-offs.