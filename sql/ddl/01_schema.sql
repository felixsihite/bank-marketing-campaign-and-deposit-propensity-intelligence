-- SQLite analytical schema.
-- Fact grain: one row per source campaign observation.
PRAGMA foreign_keys = ON;

CREATE TABLE stg_bank_marketing (
    campaign_record_id INTEGER PRIMARY KEY,
    source_row_number INTEGER NOT NULL,
    age INTEGER NOT NULL,
    job TEXT NOT NULL,
    marital TEXT NOT NULL,
    education TEXT NOT NULL,
    "default" TEXT NOT NULL,
    housing TEXT NOT NULL,
    loan TEXT NOT NULL,
    contact TEXT NOT NULL,
    month TEXT NOT NULL,
    weekday TEXT NOT NULL,
    duration INTEGER NOT NULL,
    campaign INTEGER NOT NULL,
    pdays INTEGER NOT NULL,
    previous INTEGER NOT NULL,
    poutcome TEXT NOT NULL,
    emp_var_rate REAL NOT NULL,
    cons_price_idx REAL NOT NULL,
    cons_conf_idx REAL NOT NULL,
    euribor3m REAL NOT NULL,
    nr_employed REAL NOT NULL,
    y TEXT NOT NULL,
    exact_duplicate_group_flag INTEGER NOT NULL,
    exact_duplicate_excess_flag INTEGER NOT NULL,
    conversion_flag INTEGER NOT NULL,
    age_band TEXT NOT NULL,
    previously_contacted_flag INTEGER NOT NULL,
    previous_campaign_success_flag INTEGER NOT NULL,
    campaign_contact_band TEXT NOT NULL,
    total_recorded_contacts INTEGER NOT NULL,
    contact_intensity_band TEXT NOT NULL,
    housing_loan_profile TEXT NOT NULL,
    personal_loan_profile TEXT NOT NULL,
    credit_exposure_profile TEXT NOT NULL,
    education_group TEXT NOT NULL,
    macroeconomic_regime TEXT NOT NULL,
    month_sort INTEGER NOT NULL,
    weekday_sort INTEGER NOT NULL,
    customer_profile_segment TEXT NOT NULL,
    CHECK (y IN ('yes', 'no')),
    CHECK (conversion_flag IN (0, 1)),
    CHECK (pdays BETWEEN 0 AND 999)
);

CREATE TABLE stg_propensity_scores (
    campaign_record_id INTEGER PRIMARY KEY,
    conversion_flag INTEGER NOT NULL,
    data_split TEXT NOT NULL,
    propensity_score REAL NOT NULL,
    propensity_decile INTEGER NOT NULL,
    recommended_contact_flag INTEGER NOT NULL,
    priority_tier TEXT NOT NULL,
    CHECK (propensity_score BETWEEN 0 AND 1),
    CHECK (propensity_decile BETWEEN 1 AND 10)
);

CREATE TABLE dim_customer_profile (
    customer_profile_key INTEGER PRIMARY KEY AUTOINCREMENT,
    age INTEGER NOT NULL,
    age_band TEXT NOT NULL,
    job TEXT NOT NULL,
    marital TEXT NOT NULL,
    education TEXT NOT NULL,
    education_group TEXT NOT NULL,
    default_status TEXT NOT NULL,
    housing_status TEXT NOT NULL,
    loan_status TEXT NOT NULL,
    housing_loan_profile TEXT NOT NULL,
    personal_loan_profile TEXT NOT NULL,
    credit_exposure_profile TEXT NOT NULL,
    UNIQUE (age, job, marital, education, default_status, housing_status, loan_status)
);

CREATE TABLE dim_contact (
    contact_key INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_channel TEXT NOT NULL,
    contact_month TEXT NOT NULL,
    month_sort INTEGER NOT NULL,
    contact_weekday TEXT NOT NULL,
    weekday_sort INTEGER NOT NULL,
    campaign_contact_band TEXT NOT NULL,
    contact_intensity_band TEXT NOT NULL,
    UNIQUE (contact_channel, contact_month, contact_weekday, campaign_contact_band, contact_intensity_band)
);

CREATE TABLE dim_economic_context (
    economic_context_key INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_var_rate REAL NOT NULL,
    cons_price_idx REAL NOT NULL,
    cons_conf_idx REAL NOT NULL,
    euribor3m REAL NOT NULL,
    nr_employed REAL NOT NULL,
    macroeconomic_regime TEXT NOT NULL,
    UNIQUE (emp_var_rate, cons_price_idx, cons_conf_idx, euribor3m, nr_employed)
);

CREATE TABLE fact_campaign_contact (
    campaign_record_id INTEGER PRIMARY KEY,
    customer_profile_key INTEGER NOT NULL,
    contact_key INTEGER NOT NULL,
    economic_context_key INTEGER NOT NULL,
    source_row_number INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    current_campaign_contacts INTEGER NOT NULL,
    pdays INTEGER NOT NULL,
    previous_contacts INTEGER NOT NULL,
    previous_outcome TEXT NOT NULL,
    previously_contacted_flag INTEGER NOT NULL,
    previous_campaign_success_flag INTEGER NOT NULL,
    customer_profile_segment TEXT NOT NULL,
    conversion_flag INTEGER NOT NULL,
    exact_duplicate_excess_flag INTEGER NOT NULL,
    FOREIGN KEY (customer_profile_key) REFERENCES dim_customer_profile(customer_profile_key),
    FOREIGN KEY (contact_key) REFERENCES dim_contact(contact_key),
    FOREIGN KEY (economic_context_key) REFERENCES dim_economic_context(economic_context_key)
);