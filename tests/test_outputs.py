import sqlite3

from bank_intelligence.config import DATABASE_PATH, PROCESSED_DATA_PATH


def test_output_reconciliation():
    assert PROCESSED_DATA_PATH.exists()
    assert DATABASE_PATH.exists()
    with sqlite3.connect(DATABASE_PATH) as connection:
        staging = connection.execute("SELECT COUNT(*) FROM stg_bank_marketing").fetchone()[0]
        fact = connection.execute("SELECT COUNT(*) FROM fact_campaign_contact").fetchone()[0]
        scores = connection.execute("SELECT COUNT(*) FROM mart_propensity_scores").fetchone()[0]
        positives = connection.execute("SELECT SUM(conversion_flag) FROM fact_campaign_contact").fetchone()[0]
        duplicates = connection.execute("SELECT SUM(exact_duplicate_excess_flag) FROM fact_campaign_contact").fetchone()[0]
    assert staging == fact == scores == 41188
    assert positives == 4640
    assert duplicates == 12