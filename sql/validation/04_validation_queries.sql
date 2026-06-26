-- Every query should return zero rows or the documented expected value.

-- Source-to-fact row reconciliation.
SELECT
    (SELECT COUNT(*) FROM stg_bank_marketing) AS staging_rows,
    (SELECT COUNT(*) FROM fact_campaign_contact) AS fact_rows,
    (SELECT COUNT(*) FROM mart_propensity_scores) AS score_rows;

-- Orphan foreign keys (expected: zero for every column).
SELECT
    SUM(CASE WHEN p.customer_profile_key IS NULL THEN 1 ELSE 0 END) AS orphan_profiles,
    SUM(CASE WHEN c.contact_key IS NULL THEN 1 ELSE 0 END) AS orphan_contacts,
    SUM(CASE WHEN e.economic_context_key IS NULL THEN 1 ELSE 0 END) AS orphan_economic_contexts
FROM fact_campaign_contact f
LEFT JOIN dim_customer_profile p ON p.customer_profile_key = f.customer_profile_key
LEFT JOIN dim_contact c ON c.contact_key = f.contact_key
LEFT JOIN dim_economic_context e ON e.economic_context_key = f.economic_context_key;

-- Target reconciliation (expected: 4,640 positives).
SELECT SUM(conversion_flag) AS successful_subscriptions FROM fact_campaign_contact;

-- Duplicate treatment reconciliation (expected: 12 excess duplicate observations retained).
SELECT SUM(exact_duplicate_excess_flag) AS retained_duplicate_excess_rows FROM fact_campaign_contact;

-- Propensity deciles (expected: 10 rows, near-equal observation counts).
SELECT propensity_decile, COUNT(*) AS observations, AVG(conversion_flag) AS conversion_rate
FROM mart_propensity_scores
GROUP BY propensity_decile
ORDER BY propensity_decile;