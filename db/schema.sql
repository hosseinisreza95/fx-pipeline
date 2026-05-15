-- =============================================
-- FX Pipeline - Fake DWH Schema
-- =============================================

-- ---------------------------------------------
-- Dimension: Currency Pair
-- ---------------------------------------------
CREATE TABLE IF NOT EXISTS dim_currency_pair (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    base            TEXT NOT NULL,             -- e.g. EUR
    quote           TEXT NOT NULL,             -- e.g. NOK
    pair_label      TEXT NOT NULL UNIQUE       -- e.g. EUR/NOK
);

-- ---------------------------------------------
-- Fact: FX Rates
-- ---------------------------------------------
CREATE TABLE IF NOT EXISTS fact_fx_rates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id             INTEGER NOT NULL,       -- FK to dim_currency_pair
    date                TEXT NOT NULL,          -- YYYY-MM-DD
    rate                REAL NOT NULL,          -- exchange rate for this day
    prev_day_rate       REAL,                   -- previous trading day rate
    daily_change_pct    REAL,                   -- (rate - prev_day_rate) / prev_day_rate * 100
    year_start_rate     REAL,                   -- rate on first trading day of the year
    ytd_pct             REAL,                   -- (rate - year_start_rate) / year_start_rate * 100
    ingested_at         TEXT NOT NULL,          -- pipeline run timestamp (UTC)
    FOREIGN KEY (pair_id) REFERENCES dim_currency_pair(id),
    UNIQUE (pair_id, date)                      -- prevents duplicate rows if pipeline runs twice
);