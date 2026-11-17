-- Q1. Total India imports by year, and year-on-year growth
WITH t AS (
  SELECT year, SUM(value_usd) AS value_usd
  FROM imports_clean GROUP BY year
)
SELECT year,
       ROUND(value_usd/1e6, 2) AS value_musd,
       ROUND((value_usd - LAG(value_usd) OVER (ORDER BY year)) * 100.0
             / LAG(value_usd) OVER (ORDER BY year), 1) AS yoy_pct
FROM t ORDER BY year;

-- Q2. Top 10 suppliers in 2025 with market share
SELECT partner,
       ROUND(value_usd/1e6, 2) AS value_musd,
       ROUND(share_pct, 1)     AS share_pct
FROM imports_clean
WHERE year = 2025 AND partner_type = 'Country'
ORDER BY value_usd DESC LIMIT 10;

-- Q3. Fastest-growing suppliers: 2015-2019 average vs 2021-2025 average
--     (only suppliers above $1M in the later period)
WITH a AS (
  SELECT partner,
         AVG(CASE WHEN year BETWEEN 2015 AND 2019 THEN value_usd END) AS early_avg,
         AVG(CASE WHEN year BETWEEN 2021 AND 2025 THEN value_usd END) AS late_avg
  FROM imports_clean WHERE partner_type = 'Country'
  GROUP BY partner
)
SELECT partner,
       ROUND(early_avg/1e6, 2) AS early_musd,
       ROUND(late_avg/1e6, 2)  AS late_musd,
       ROUND((late_avg - early_avg) * 100.0 / early_avg, 0) AS growth_pct
FROM a
WHERE early_avg > 0 AND late_avg > 1e6
ORDER BY growth_pct DESC LIMIT 10;

-- Q4. Japan vs the top 4 suppliers: value and share by year
SELECT year, partner, ROUND(value_usd/1e6, 3) AS value_musd, ROUND(share_pct, 2) AS share_pct
FROM imports_clean
WHERE partner IN ('Japan','China','Italy','Germany','USA')
ORDER BY partner, year;

-- Q5. Average value per unit in 2025 (suppliers above 1M USD)
--     Note: "unit" mixes small and large machines, so this shows product mix, not a pure price premium.
SELECT partner,
       ROUND(value_usd/1e6, 2) AS value_musd,
       qty_units,
       ROUND(usd_per_unit, 0)  AS usd_per_unit
FROM imports_clean
WHERE year = 2025 AND partner_type = 'Country' AND value_usd > 1e6
ORDER BY usd_per_unit DESC;

-- Q6. Supplier concentration: share of the top 3 suppliers each year
SELECT year, ROUND(SUM(share_pct), 1) AS top3_share_pct
FROM (
  SELECT year, share_pct,
         ROW_NUMBER() OVER (PARTITION BY year ORDER BY value_usd DESC) AS rn
  FROM imports_clean WHERE partner_type = 'Country'
)
WHERE rn <= 3 GROUP BY year ORDER BY year;
