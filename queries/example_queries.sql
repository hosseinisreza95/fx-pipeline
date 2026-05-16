-- =============================================
-- FX Pipeline - Example Queries
-- =============================================
-- Two versions:
-- Section A: SQLite (local version)
-- Section B: BigQuery (production version)
-- =============================================


-- =============================================
-- SECTION A: SQLite Queries (pipeline/)
-- =============================================

-- ---------------------------------------------
-- A1. Lookup: rate for a specific pair on a specific date
-- ---------------------------------------------
SELECT
    p.pair_label,
    f.date,
    f.rate
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE p.pair_label = 'EUR/NOK'
  AND f.date = '2025-06-15';


-- ---------------------------------------------
-- A2. Daily change: day-over-day % change for a pair
-- ---------------------------------------------
SELECT
    p.pair_label,
    f.date,
    f.rate,
    f.prev_day_rate,
    ROUND(f.daily_change_pct, 4) AS daily_change_pct
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE p.pair_label = 'EUR/NOK'
  AND f.date BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY f.date;


-- ---------------------------------------------
-- A3. YTD: year-to-date % change for a pair
-- ---------------------------------------------
SELECT
    p.pair_label,
    f.date,
    f.rate,
    f.year_start_rate,
    ROUND(f.ytd_pct, 4) AS ytd_pct
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE p.pair_label = 'EUR/NOK'
  AND f.date BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY f.date;


-- ---------------------------------------------
-- A4. Most volatile pairs (highest avg daily change)
-- ---------------------------------------------
SELECT
    p.pair_label,
    ROUND(AVG(ABS(f.daily_change_pct)), 4) AS avg_daily_volatility
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE f.date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY p.pair_label
ORDER BY avg_daily_volatility DESC
LIMIT 10;


-- =============================================
-- SECTION B: BigQuery Queries (pipeline_gcp/)
-- Project: fx-pipeline-496417
-- Dataset: fx_dwh
-- Table: fact_fx_rates
-- =============================================

-- ---------------------------------------------
-- B1. Lookup: rate for a specific pair on a specific date
-- ---------------------------------------------
SELECT
    pair_label,
    date,
    rate
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE pair_label = 'EUR/NOK'
  AND date = '2025-06-15';


-- ---------------------------------------------
-- B2. Latest rates for all pairs
-- ---------------------------------------------
SELECT
    pair_label,
    date,
    rate,
    ROUND(daily_change_pct, 4) AS daily_change_pct,
    ROUND(ytd_pct, 4)          AS ytd_pct
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE date = (SELECT MAX(date) FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`)
ORDER BY pair_label;


-- ---------------------------------------------
-- B3. Daily change: day-over-day % change for a pair
-- ---------------------------------------------
SELECT
    pair_label,
    date,
    rate,
    prev_day_rate,
    ROUND(daily_change_pct, 4) AS daily_change_pct
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE pair_label = 'EUR/NOK'
  AND date BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY date;


-- ---------------------------------------------
-- B4. YTD: year-to-date % change for a pair
-- ---------------------------------------------
SELECT
    pair_label,
    date,
    rate,
    year_start_rate,
    ROUND(ytd_pct, 4) AS ytd_pct
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE pair_label = 'EUR/NOK'
  AND date BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY date;


-- ---------------------------------------------
-- B5. Best and worst performing pairs YTD
-- ---------------------------------------------
SELECT
    pair_label,
    rate,
    year_start_rate,
    ROUND(ytd_pct, 4) AS ytd_pct
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE date = (SELECT MAX(date) FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`)
ORDER BY ytd_pct DESC;


-- ---------------------------------------------
-- B6. Monthly average rate for a pair
-- ---------------------------------------------
SELECT
    pair_label,
    FORMAT_DATE('%Y-%m', date)  AS month,
    ROUND(AVG(rate), 4)         AS avg_rate,
    ROUND(MIN(rate), 4)         AS min_rate,
    ROUND(MAX(rate), 4)         AS max_rate
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE pair_label = 'EUR/NOK'
  AND date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY pair_label, month
ORDER BY month;


-- ---------------------------------------------
-- B7. Most volatile pairs (highest avg daily change)
-- ---------------------------------------------
SELECT
    pair_label,
    ROUND(AVG(ABS(daily_change_pct)), 4) AS avg_daily_volatility
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
WHERE date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY pair_label
ORDER BY avg_daily_volatility DESC
LIMIT 10;


-- ---------------------------------------------
-- B8. No duplicates check
-- ---------------------------------------------
SELECT
    pair_label,
    date,
    COUNT(*) as count
FROM `fx-pipeline-496417.fx_dwh.fact_fx_rates`
GROUP BY pair_label, date
HAVING COUNT(*) > 1;