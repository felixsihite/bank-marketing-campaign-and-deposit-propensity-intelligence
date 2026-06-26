import sqlite3

from bank_intelligence.config import DATABASE_PATH


def test_star_schema_keys_and_business_marts():
    with sqlite3.connect(DATABASE_PATH) as connection:
        facts = connection.execute("SELECT COUNT(*) FROM fact_campaign_contact").fetchone()[0]
        scores = connection.execute("SELECT COUNT(*) FROM mart_propensity_scores").fetchone()[0]
        orphan_contacts = connection.execute(
            "SELECT COUNT(*) FROM fact_campaign_contact f LEFT JOIN dim_contact d "
            "ON f.contact_key=d.contact_key WHERE d.contact_key IS NULL"
        ).fetchone()[0]
        orphan_economics = connection.execute(
            "SELECT COUNT(*) FROM fact_campaign_contact f LEFT JOIN dim_economic_context d "
            "ON f.economic_context_key=d.economic_context_key WHERE d.economic_context_key IS NULL"
        ).fetchone()[0]
        executive_metrics = connection.execute("SELECT COUNT(*) FROM mart_executive_kpi").fetchone()[0]
        campaign_dimensions = connection.execute(
            "SELECT COUNT(DISTINCT performance_dimension) FROM mart_campaign_performance"
        ).fetchone()[0]

    assert facts == scores == 41188
    assert orphan_contacts == orphan_economics == 0
    assert executive_metrics == 7
    assert campaign_dimensions == 6