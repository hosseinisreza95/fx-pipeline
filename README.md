# FX Pipeline

A daily pipeline that fetches foreign-exchange rates for 7 currencies, stores them in BigQuery, and makes them available for analysis via a live dashboard.

**Live Dashboard:** https://datastudio.google.com/s/k5X10e8yiQI

> Rates were validated against ECB (European Central Bank) reference rates and matched exactly, confirming data accuracy.

---

## What it does

- Fetches daily FX rates from [frankfurter.app](https://frankfurter.app) (ECB data source)
- Computes **42 cross-pairs** across 7 currencies
- Calculates **YTD** (Year-to-Date) and **daily change %** for each pair
- Loads data into BigQuery
- Runs automatically every day at 17:00 CET via Cloud Scheduler

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

---

## YTD Definition

Year-to-Date change is calculated from the first available trading day of the year:

```
YTD % = (rate_today - rate_jan1) / rate_jan1 × 100
```

---

## Project Structure

```
fx-pipeline/
├── pipeline/                  # Local version (SQLite)
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── run_pipeline.py
├── pipeline_gcp/              # Production version (BigQuery)
│   ├── components/
│   │   ├── extract.py
│   │   ├── transform.py
│   │   └── load_bq.py
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
├── requirements.txt
└── design_notes.md
```

---

## How to Run

### Option A — GCP (production)

**Requirements:** Google Cloud account, `gcloud` CLI, BigQuery dataset

```bash
# authenticate
gcloud auth application-default login

# historical load (first time)
python pipeline_gcp/main.py --mode historical --start 2025-01-01 --end 2025-12-31

# daily load
python pipeline_gcp/main.py --mode daily
```

### Option B — Local (SQLite + Docker)

```bash
# build
docker build -t fx-pipeline .

# historical load
docker run -v ${PWD}/db:/app/db fx-pipeline \
  python pipeline/run_pipeline.py --mode historical \
  --start 2025-01-01 --end 2025-12-31

# daily load
docker run -v ${PWD}/db:/app/db fx-pipeline
```

---

## Cloud Deployment (GCP)

```
Cloud Scheduler (17:00 CET daily)
        ↓
Cloud Run Job
        ↓
Docker Container (pipeline_gcp/main.py --mode daily)
        ↓
BigQuery (fx_dwh.fact_fx_rates)
        ↓
Looker Studio Dashboard
```

**Infrastructure:**
- Docker image stored in Artifact Registry
- Pipeline runs as a Cloud Run Job
- Scheduled daily via Cloud Scheduler
- Data served to Looker Studio directly from BigQuery

---

## Validate Output

```sql
-- row count
SELECT COUNT(*) FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`;

-- latest rates
SELECT pair_label, date, rate, daily_change_pct, ytd_pct
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE date = (SELECT MAX(date) FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`)
ORDER BY pair_label;

-- no duplicates check
SELECT pair_label, date, COUNT(*)
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
GROUP BY pair_label, date
HAVING COUNT(*) > 1;
```

See `queries/example_queries.sql` for more examples.

---

## Design Decisions

See `design_notes.md` for key decisions and trade-offs.