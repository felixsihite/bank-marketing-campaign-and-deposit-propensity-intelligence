-- Deterministic dimension and fact materialization from validated staging.
INSERT INTO dim_customer_profile (
    age, age_band, job, marital, education, education_group, default_status,
    housing_status, loan_status, housing_loan_profile, personal_loan_profile,
    credit_exposure_profile
)
SELECT DISTINCT
    age, age_band, job, marital, education, education_group, "default",
    housing, loan, housing_loan_profile, personal_loan_profile,
    credit_exposure_profile
FROM stg_bank_marketing;

INSERT INTO dim_contact (
    contact_channel, contact_month, month_sort, contact_weekday, weekday_sort,
    campaign_contact_band, contact_intensity_band
)
SELECT DISTINCT
    contact, month, month_sort, weekday, weekday_sort,
    campaign_contact_band, contact_intensity_band
FROM stg_bank_marketing;

INSERT INTO dim_economic_context (
    emp_var_rate, cons_price_idx, cons_conf_idx, euribor3m, nr_employed, macroeconomic_regime
)
SELECT DISTINCT
    emp_var_rate, cons_price_idx, cons_conf_idx, euribor3m, nr_employed, macroeconomic_regime
FROM stg_bank_marketing;

INSERT INTO fact_campaign_contact (
    campaign_record_id, customer_profile_key, contact_key, economic_context_key,
    source_row_number, duration_seconds, current_campaign_contacts, pdays,
    previous_contacts, previous_outcome, previously_contacted_flag,
    previous_campaign_success_flag, customer_profile_segment, conversion_flag,
    exact_duplicate_excess_flag
)
SELECT
    s.campaign_record_id,
    p.customer_profile_key,
    c.contact_key,
    e.economic_context_key,
    s.source_row_number,
    s.duration,
    s.campaign,
    s.pdays,
    s.previous,
    s.poutcome,
    s.previously_contacted_flag,
    s.previous_campaign_success_flag,
    s.customer_profile_segment,
    s.conversion_flag,
    s.exact_duplicate_excess_flag
FROM stg_bank_marketing s
JOIN dim_customer_profile p
  ON p.age = s.age AND p.job = s.job AND p.marital = s.marital
 AND p.education = s.education AND p.default_status = s."default"
 AND p.housing_status = s.housing AND p.loan_status = s.loan
JOIN dim_contact c
  ON c.contact_channel = s.contact AND c.contact_month = s.month
 AND c.contact_weekday = s.weekday AND c.campaign_contact_band = s.campaign_contact_band
 AND c.contact_intensity_band = s.contact_intensity_band
JOIN dim_economic_context e
  ON e.emp_var_rate = s.emp_var_rate AND e.cons_price_idx = s.cons_price_idx
 AND e.cons_conf_idx = s.cons_conf_idx AND e.euribor3m = s.euribor3m
 AND e.nr_employed = s.nr_employed;

CREATE INDEX idx_fact_customer_profile ON fact_campaign_contact(customer_profile_key);
CREATE INDEX idx_fact_contact ON fact_campaign_contact(contact_key);
CREATE INDEX idx_fact_economic_context ON fact_campaign_contact(economic_context_key);
CREATE INDEX idx_fact_conversion ON fact_campaign_contact(conversion_flag);
CREATE INDEX idx_stg_profile_segment ON stg_bank_marketing(customer_profile_segment);