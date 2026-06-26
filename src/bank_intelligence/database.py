from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def build_database(
    processed: pd.DataFrame,
    predictions: pd.DataFrame,
    database_path: Path,
    ddl_path: Path,
    transformation_path: Path,
    marts_path: Path,
) -> None:
    if database_path.exists():
        database_path.unlink()
    with sqlite3.connect(database_path) as connection:
        connection.executescript(ddl_path.read_text(encoding="utf-8"))
        source = processed.rename(columns={
            "day_of_week": "weekday", "emp.var.rate": "emp_var_rate",
            "cons.price.idx": "cons_price_idx", "cons.conf.idx": "cons_conf_idx",
            "nr.employed": "nr_employed",
        })
        source.to_sql("stg_bank_marketing", connection, if_exists="append", index=False)
        predictions.to_sql("stg_propensity_scores", connection, if_exists="append", index=False)
        connection.executescript(transformation_path.read_text(encoding="utf-8"))
        connection.executescript(marts_path.read_text(encoding="utf-8"))
        connection.commit()
        export_dir = database_path.parents[1] / "data" / "processed" / "powerbi"
        export_dir.mkdir(parents=True, exist_ok=True)
        exports = {
            "dim_customer_profile": "SELECT * FROM dim_customer_profile",
            "dim_contact": "SELECT * FROM dim_contact",
            "dim_economic_context": "SELECT * FROM dim_economic_context",
            "fact_campaign_contact": """
                SELECT f.*, p.propensity_score, p.propensity_decile,
                       p.recommended_contact_flag, p.priority_tier, p.data_split
                FROM fact_campaign_contact f
                JOIN mart_propensity_scores p USING (campaign_record_id)
            """,
        }
        for name, query in exports.items():
            pd.read_sql_query(query, connection).to_csv(export_dir / f"{name}.csv", index=False)


def validate_database(database_path: Path) -> dict[str, int]:
    with sqlite3.connect(database_path) as connection:
        tables = [
            "stg_bank_marketing", "dim_customer_profile", "dim_contact",
            "dim_economic_context", "fact_campaign_contact", "mart_propensity_scores",
        ]
        counts = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in tables
        }
        orphan_profile = int(connection.execute(
            "SELECT COUNT(*) FROM fact_campaign_contact f LEFT JOIN dim_customer_profile d "
            "ON f.customer_profile_key=d.customer_profile_key WHERE d.customer_profile_key IS NULL"
        ).fetchone()[0])
        counts["orphan_profile_keys"] = orphan_profile
        return counts