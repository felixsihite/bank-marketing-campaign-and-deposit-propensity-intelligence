from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def performance_table(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    summary = (
        frame.groupby(dimension, observed=True, dropna=False)["conversion_flag"]
        .agg(observations="size", subscriptions="sum", conversion_rate="mean")
        .reset_index()
    )
    return summary.sort_values(["conversion_rate", "observations"], ascending=[False, False])


def build_analytics(frame: pd.DataFrame, output_dir: Path) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dimensions = [
        "age_band", "job", "marital", "education_group", "housing_loan_profile",
        "personal_loan_profile", "credit_exposure_profile", "contact", "month",
        "day_of_week", "campaign_contact_band", "poutcome", "macroeconomic_regime",
        "customer_profile_segment",
    ]
    tables = {dimension: performance_table(frame, dimension) for dimension in dimensions}
    for name, table in tables.items():
        table.to_csv(output_dir / f"performance_by_{name}.csv", index=False)

    kpis = {
        "campaign_observations": int(len(frame)),
        "successful_subscriptions": int(frame["conversion_flag"].sum()),
        "conversion_rate": float(frame["conversion_flag"].mean()),
        "average_campaign_contacts": float(frame["campaign"].mean()),
        "median_campaign_contacts": float(frame["campaign"].median()),
        "previously_contacted_rate": float(frame["previously_contacted_flag"].mean()),
        "previous_campaign_success_rate": float(frame["previous_campaign_success_flag"].mean()),
        "cellular_conversion_rate": float(frame.loc[frame["contact"].eq("cellular"), "conversion_flag"].mean()),
        "telephone_conversion_rate": float(frame.loc[frame["contact"].eq("telephone"), "conversion_flag"].mean()),
    }
    (output_dir / "executive_kpis.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    return tables