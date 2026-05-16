# Design Notes

## Key Decisions and Trade-offs

---

### 1. Data Source: frankfurter.app

**Decision:** Used frankfurter.app as the FX data source.

**Reasons:**
- Free, no API key required
- Covers all required currencies (NOK, EUR, SEK, PLN, RON, DKK, CZK)
- Provides historical data back to 1999
- Data is sourced directly from the European Central Bank (ECB)

**Trade-off:** Not a real-time source. Data updates once per business day
around 16:00 CET. Pipeline is scheduled at 17:00 CET to ensure fresh data
is always available.

---

### 2. Schema Design

**SQLite version (local):** Star Schema with `dim_currency_pair` and `fact_fx_rates`.

**BigQuery version (production):** Flat/denormalized table — all fields in `fact_fx_rates`.

**Why denormalized in BigQuery?**
- BigQuery is optimized for flat, wide tables
- Joins are expensive at scale in BigQuery
- Denormalization is standard practice for analytical warehouses

**Trade-off:** `dim_currency` table was omitted as currency metadata is
embedded directly. Can be added if currency-level attributes are needed.

---

### 3. Pre-computed Metrics

**Decision:** `daily_change_pct`, `year_start_rate`, and `ytd_pct` are
computed at load time and stored in the fact table.

**Reasons:**
- Query simplicity — no complex window functions needed at query time
- Follows warehouse best practices (pre-aggregate where possible)
- At ~42 rows/day the storage cost is negligible

**Trade-off:** Redundant data in the fact table. If business logic
changes (e.g. YTD definition changes), historical rows would need
to be recomputed.

---

### 4. YTD Definition

**Decision:** YTD is defined as percentage change from the first
available trading day of the year to the current date.

```
YTD % = (rate_today - rate_year_start) / rate_year_start × 100
```

**Note:** Year start is the first trading day of each year
(not necessarily January 1st, as markets are closed on weekends
and public holidays). Works automatically for any date range
across multiple years.

---

### 5. All 42 Cross-pairs Pre-computed

**Decision:** All cross-pairs among the 7 currencies are computed
at extract time (7 × 6 = 42 pairs).

**Reasons:**
- Avoids complex calculations at query time
- Makes it easy to look up any pair directly
- Consistent with how FX data is typically stored in a warehouse

**Trade-off:** 42 rows per trading day instead of 7. At ~10,920 rows/year
this is negligible.

---

### 6. Idempotency

**Decision:** Pipeline is idempotent — safe to run multiple times
without creating duplicate data.

**SQLite:** `UNIQUE (pair_id, date)` constraint + `INSERT OR IGNORE`

**BigQuery:** `WRITE_APPEND` with date-based deduplication via query filters.
Duplicate runs on the same day result in duplicate rows — acceptable for
daily batch pipelines where reruns are rare.

---

### 7. Two Versions: SQLite and BigQuery

**Decision:** Project ships two versions of the pipeline.

| | SQLite (pipeline/) | BigQuery (pipeline_gcp/) |
|---|---|---|
| Use case | Local dev / testing | Production |
| Warehouse | SQLite file | Google BigQuery |
| Orchestration | Prefect / Docker | Cloud Run + Cloud Scheduler |
| Dashboard | DB Browser | Looker Studio |

**Reason:** SQLite version allows anyone to run and validate the pipeline
locally without a cloud account. BigQuery version is the production deployment.

---

### 8. Pipeline Modes

**Decision:** Pipeline supports two modes — `historical` and `daily`.

- `historical`: loads a custom date range (first time setup / backfill)
- `daily`: loads yesterday's data (scheduled run)

---

### 9. Cloud Deployment: GCP

**Decision:** Used Google Cloud Platform for production deployment.

**Components:**
- **Artifact Registry** — stores Docker image
- **Cloud Run Job** — runs the pipeline in a container
- **Cloud Scheduler** — triggers daily at 17:00 CET (16:00 UTC)
- **BigQuery** — data warehouse
- **Looker Studio** — dashboard, connected directly to BigQuery

**Why 17:00 CET?**
frankfurter.app updates at 16:00 CET. Pipeline runs one hour later
to ensure fresh data is always available.

**Trade-off:** GCP adds infrastructure complexity. Mitigated by also
providing a local Docker version that runs without any cloud account.

---

### 10. Data Validation

Rates were validated against ECB (European Central Bank) reference rates
and matched exactly, confirming data accuracy. frankfurter.app uses ECB
as its primary data source, so this was expected.