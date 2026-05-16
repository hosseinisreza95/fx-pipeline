# Design Notes

## Key Decisions and Trade-offs

---

### 1. Data Source: frankfurter.app

**Decision:** Used frankfurter.app as the FX data source.

**Reasons:**
- Free, no API key required
- Covers all required currencies (NOK, EUR, SEK, PLN, RON, DKK, CZK)
- Provides historical data back to 1999
- Returns cross-pairs directly

**Trade-off:** Not a real-time source. Data is available with a 1-day lag,
which is acceptable for a daily batch pipeline.

---

### 2. Schema: Star Schema (Kimball)

**Decision:** Used a Star Schema with `dim_currency_pair` and `fact_fx_rates`.

**Reasons:**
- Standard warehouse pattern — easy to join with other DWH tables
- Queries are simple and readable
- Scales well as more currencies or metrics are added

**Trade-off:** `dim_currency` table was omitted as currency metadata is
embedded in `dim_currency_pair`. Can be added if the DWH grows and
currency-level attributes are needed.

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

**Implementation:** `UNIQUE (pair_id, date)` constraint on `fact_fx_rates`
combined with `INSERT OR IGNORE` ensures no duplicates even if the
pipeline runs twice on the same day.

---

### 7. SQLite for Fake DWH

**Decision:** Used SQLite as the warehouse backend.

**Reasons:**
- Portable — single file, no server required
- Easy to validate — can be opened with DB Browser for SQLite
- Sufficient for a fake DWH demonstration

**In production:** Would be replaced with Azure SQL Database or
Snowflake. Schema and queries are standard SQL and would work
without modification.

---

### 8. Pipeline Modes

**Decision:** Pipeline supports two modes — `historical` and `daily`.

- `historical`: loads a custom date range (first time setup)
- `daily`: loads yesterday's data (scheduled run)

This allows the pipeline to be used both for backfilling and
for ongoing daily ingestion.

---

### 9. Docker Containerization

**Decision:** Pipeline is fully containerized with Docker.

**Reasons:**
- Consistent execution environment across local, CI, and cloud
- Easy to deploy to Azure Container Instance or any cloud provider
- No dependency conflicts — everything is isolated inside the container
- SQLite file is mounted as a volume so data persists between runs

**Trade-off:** Adds complexity for local development. Mitigated by
also supporting a local run option without Docker (see README).

**In production:** Docker image would be pushed to Azure Container Registry
and triggered daily by Azure Data Factory.