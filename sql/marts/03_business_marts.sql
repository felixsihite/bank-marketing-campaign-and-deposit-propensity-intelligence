-- KPI values are source-supported only; no fabricated financial metrics.
CREATE VIEW mart_executive_kpi AS
SELECT 'Total Campaign Observations' AS metric_name, COUNT(*) * 1.0 AS metric_value, 'integer' AS metric_format FROM fact_campaign_contact
UNION ALL SELECT 'Successful Deposit Subscriptions', SUM(conversion_flag) * 1.0, 'integer' FROM fact_campaign_contact
UNION ALL SELECT 'Deposit Conversion Rate', AVG(conversion_flag), 'percentage' FROM fact_campaign_contact
UNION ALL SELECT 'Average Campaign Contacts', AVG(current_campaign_contacts), 'decimal' FROM fact_campaign_contact
UNION ALL SELECT 'Median Campaign Contacts', AVG(current_campaign_contacts), 'decimal' FROM (
    SELECT current_campaign_contacts,
           ROW_NUMBER() OVER (ORDER BY current_campaign_contacts) AS row_number,
           COUNT(*) OVER () AS row_count
    FROM fact_campaign_contact
) WHERE row_number IN ((row_count + 1) / 2, (row_count + 2) / 2)
UNION ALL SELECT 'Previously Contacted Rate', AVG(previously_contacted_flag), 'percentage' FROM fact_campaign_contact
UNION ALL SELECT 'Previous Campaign Success Rate', AVG(previous_campaign_success_flag), 'percentage' FROM fact_campaign_contact;

CREATE VIEW mart_customer_segment_performance AS
SELECT
    s.customer_profile_segment,
    s.age_band,
    s.job,
    s.education_group,
    s.credit_exposure_profile,
    COUNT(*) AS campaign_observations,
    SUM(s.conversion_flag) AS successful_subscriptions,
    AVG(s.conversion_flag) AS conversion_rate
FROM stg_bank_marketing s
GROUP BY s.customer_profile_segment, s.age_band, s.job, s.education_group, s.credit_exposure_profile;

CREATE VIEW mart_campaign_performance AS
SELECT 'contact_channel' AS performance_dimension, contact AS performance_member,
       COUNT(*) AS campaign_observations, SUM(conversion_flag) AS successful_subscriptions,
       AVG(conversion_flag) AS conversion_rate
FROM stg_bank_marketing GROUP BY contact
UNION ALL
SELECT 'month', month, COUNT(*), SUM(conversion_flag), AVG(conversion_flag)
FROM stg_bank_marketing GROUP BY month
UNION ALL
SELECT 'weekday', weekday, COUNT(*), SUM(conversion_flag), AVG(conversion_flag)
FROM stg_bank_marketing GROUP BY weekday
UNION ALL
SELECT 'contact_frequency', campaign_contact_band, COUNT(*), SUM(conversion_flag), AVG(conversion_flag)
FROM stg_bank_marketing GROUP BY campaign_contact_band
UNION ALL
SELECT 'previous_outcome', poutcome, COUNT(*), SUM(conversion_flag), AVG(conversion_flag)
FROM stg_bank_marketing GROUP BY poutcome
UNION ALL
SELECT 'macroeconomic_regime', macroeconomic_regime, COUNT(*), SUM(conversion_flag), AVG(conversion_flag)
FROM stg_bank_marketing GROUP BY macroeconomic_regime;

CREATE TABLE mart_propensity_scores AS
SELECT
    p.campaign_record_id,
    p.data_split,
    p.propensity_score,
    p.propensity_decile,
    p.recommended_contact_flag,
    p.priority_tier,
    f.conversion_flag,
    f.customer_profile_key,
    f.contact_key,
    f.economic_context_key
FROM stg_propensity_scores p
JOIN fact_campaign_contact f ON f.campaign_record_id = p.campaign_record_id;

CREATE UNIQUE INDEX idx_propensity_campaign ON mart_propensity_scores(campaign_record_id);
CREATE INDEX idx_propensity_decile ON mart_propensity_scores(propensity_decile);
CREATE INDEX idx_propensity_recommendation ON mart_propensity_scores(recommended_contact_flag);