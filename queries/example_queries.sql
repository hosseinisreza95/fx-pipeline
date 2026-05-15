-- =============================================
-- FX Pipeline - Example Queries
-- =============================================


-- ---------------------------------------------
-- 1. Lookup: rate for a specific pair on a specific date
-- ---------------------------------------------
SELECT
    p.pair_label,
    f.date,
    f.rate
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE p.pair_label = 'EUR/NOK'
  AND f.date = '2024-06-15';


-- ---------------------------------------------
-- 2. Lookup: all rates for a specific date
-- ---------------------------------------------
SELECT
    p.pair_label,
    f.date,
    f.rate
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE f.date = '2024-06-15'
ORDER BY p.pair_label;


-- ---------------------------------------------
-- 3. Daily change: day-over-day % change for a pair
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
  AND f.date BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY f.date;


-- ---------------------------------------------
-- 4. YTD: year-to-date % change for a pair
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
  AND f.date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY f.date;


-- ---------------------------------------------
-- 5. YTD summary: best and worst performing pairs at end of year
-- ---------------------------------------------
SELECT
    p.pair_label,
    f.rate,
    f.year_start_rate,
    ROUND(f.ytd_pct, 4) AS ytd_pct
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE f.date = (SELECT MAX(date) FROM fact_fx_rates WHERE strftime('%Y', date) = '2024')
ORDER BY f.ytd_pct DESC;


-- ---------------------------------------------
-- 6. Monthly average rate for a pair
-- ---------------------------------------------
SELECT
    p.pair_label,
    strftime('%Y-%m', f.date) AS month,
    ROUND(AVG(f.rate), 4)     AS avg_rate,
    ROUND(MIN(f.rate), 4)     AS min_rate,
    ROUND(MAX(f.rate), 4)     AS max_rate
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE p.pair_label = 'EUR/NOK'
  AND f.date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY strftime('%Y-%m', f.date)
ORDER BY month;


-- ---------------------------------------------
-- 7. Most volatile pairs (highest avg daily change)
-- useful for risk analysis
-- ---------------------------------------------
SELECT
    p.pair_label,
    ROUND(AVG(ABS(f.daily_change_pct)), 4) AS avg_daily_volatility
FROM fact_fx_rates f
JOIN dim_currency_pair p ON f.pair_id = p.id
WHERE f.date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY p.pair_label
ORDER BY avg_daily_volatility DESC
LIMIT 10;