from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, precision_score, recall_score


EPSILON = 1e-6


def numeric_psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    expected_clean = pd.to_numeric(expected, errors="coerce").dropna()
    actual_clean = pd.to_numeric(actual, errors="coerce").dropna()
    if expected_clean.empty or actual_clean.empty:
        return float("nan")
    quantiles = np.unique(expected_clean.quantile(np.linspace(0, 1, bins + 1)).to_numpy())
    if len(quantiles) <= 2:
        return 0.0 if np.isclose(expected_clean.mean(), actual_clean.mean()) else 1.0
    edges = np.concatenate(([-np.inf], quantiles[1:-1], [np.inf]))
    expected_counts, _ = np.histogram(expected_clean.to_numpy(dtype=float), bins=edges)
    actual_counts, _ = np.histogram(actual_clean.to_numpy(dtype=float), bins=edges)
    expected_values = expected_counts / expected_counts.sum() + EPSILON
    actual_values = actual_counts / actual_counts.sum() + EPSILON
    return float(np.sum((actual_values - expected_values) * np.log(actual_values / expected_values)))


def categorical_psi(expected: pd.Series, actual: pd.Series) -> float:
    expected_distribution = expected.astype(str).value_counts(normalize=True)
    actual_distribution = actual.astype(str).value_counts(normalize=True)
    categories = expected_distribution.index.union(actual_distribution.index)
    expected_values = expected_distribution.reindex(categories, fill_value=0).to_numpy() + EPSILON
    actual_values = actual_distribution.reindex(categories, fill_value=0).to_numpy() + EPSILON
    return float(np.sum((actual_values - expected_values) * np.log(actual_values / expected_values)))


def expected_calibration_error(evaluation: pd.DataFrame, bins: int = 10) -> float:
    working = evaluation.copy()
    working["calibration_bin"] = pd.qcut(
        working["evaluation_probability"].rank(method="first"), bins, duplicates="drop",
    )
    grouped = working.groupby("calibration_bin", observed=True).agg(
        observations=("conversion_flag", "size"),
        mean_probability=("evaluation_probability", "mean"),
        observed_rate=("conversion_flag", "mean"),
    )
    weights = grouped["observations"] / grouped["observations"].sum()
    return float((weights * (grouped["mean_probability"] - grouped["observed_rate"]).abs()).sum())


def _drift_status(psi: float) -> str:
    if psi >= 0.25:
        return "high"
    if psi >= 0.10:
        return "moderate"
    return "stable"


def _subgroup_table(evaluation: pd.DataFrame, threshold: float) -> pd.DataFrame:
    dimensions = ["age_band", "job", "marital", "education_group", "contact", "poutcome"]
    rows: list[dict[str, Any]] = []
    for dimension in dimensions:
        for member, group in evaluation.groupby(dimension, observed=True, dropna=False):
            actual = group["conversion_flag"].astype(int)
            predicted = group["evaluation_probability"].ge(threshold).astype(int)
            rows.append({
                "dimension": dimension,
                "member": str(member),
                "observations": int(len(group)),
                "positives": int(actual.sum()),
                "base_rate": float(actual.mean()),
                "average_score": float(group["evaluation_probability"].mean()),
                "predicted_positive_rate": float(predicted.mean()),
                "precision": float(precision_score(actual, predicted, zero_division=0)),
                "recall": float(recall_score(actual, predicted, zero_division=0)),
                "brier_score": float(brier_score_loss(actual, group["evaluation_probability"])),
                "minimum_volume_pass": bool(len(group) >= 100),
            })
    return pd.DataFrame(rows).sort_values(["dimension", "observations"], ascending=[True, False])


def generate_governance_reports(
    frame: pd.DataFrame,
    scored: pd.DataFrame,
    evaluation_scores_path: Path,
    metrics: dict[str, Any],
    reports_dir: Path,
) -> dict[str, Any]:
    evaluation_scores = pd.read_csv(evaluation_scores_path)
    evaluation = evaluation_scores.merge(
        frame,
        on=["campaign_record_id", "conversion_flag"],
        validate="one_to_one",
    )
    split_frame = frame.merge(
        scored[["campaign_record_id", "data_split"]],
        on="campaign_record_id",
        validate="one_to_one",
    )
    expected = split_frame[split_frame["data_split"].eq("model_fit_train")]
    actual = split_frame[split_frame["data_split"].eq("locked_test")]

    numeric_features = ["age", "campaign", "previous", "euribor3m", "nr.employed"]
    categorical_features = ["job", "contact", "month", "age_band", "poutcome", "education_group"]
    drift_rows = []
    for feature in numeric_features:
        psi = numeric_psi(expected[feature], actual[feature])
        drift_rows.append({"feature": feature, "feature_type": "numeric", "psi": psi, "status": _drift_status(psi)})
    for feature in categorical_features:
        psi = categorical_psi(expected[feature], actual[feature])
        drift_rows.append({
            "feature": feature,
            "feature_type": "categorical",
            "psi": psi,
            "status": _drift_status(psi),
        })
    drift = pd.DataFrame(drift_rows).sort_values("psi", ascending=False)
    drift.to_csv(reports_dir / "drift_monitoring.csv", index=False)

    subgroup = _subgroup_table(evaluation, metrics["recommended_threshold"])
    subgroup.to_csv(reports_dir / "subgroup_performance.csv", index=False)
    eligible = subgroup[subgroup["minimum_volume_pass"]]
    ece = expected_calibration_error(evaluation_scores)
    governance = {
        "evaluation_scope": "Locked test only; 20% stratified holdout not used for model selection or threshold tuning.",
        "locked_test_observations": int(len(evaluation_scores)),
        "expected_calibration_error": ece,
        "max_psi": float(drift["psi"].max()),
        "drift_status": _drift_status(float(drift["psi"].max())),
        "subgroup_minimum_volume": 100,
        "eligible_subgroup_count": int(len(eligible)),
        "eligible_subgroup_recall_range": [
            float(eligible["recall"].min()),
            float(eligible["recall"].max()),
        ],
        "eligible_subgroup_precision_range": [
            float(eligible["precision"].min()),
            float(eligible["precision"].max()),
        ],
        "protected_attribute_note": (
            "Gender, race, religion, disability, and other protected attributes are unavailable; "
            "this is performance slicing, not a complete fairness audit."
        ),
        "monitoring_thresholds": {
            "stable": "PSI < 0.10",
            "moderate": "0.10 <= PSI < 0.25",
            "high": "PSI >= 0.25",
        },
    }
    (reports_dir / "model_governance.json").write_text(json.dumps(governance, indent=2), encoding="utf-8")
    markdown = f"""# Model Governance Report

## Evaluation Boundary

All performance, calibration, subgroup, and decile metrics in this report use the **locked test set only** ({len(evaluation_scores):,} observations). Full-portfolio propensity scores are operational ranking outputs and are not used as unbiased performance evidence.

## Monitoring Summary

| Control | Result | Interpretation |
|---|---:|---|
| Expected calibration error | {ece:.3f} | Lower is better; monitor after deployment |
| Maximum train-to-test PSI | {drift['psi'].max():.3f} | {_drift_status(float(drift['psi'].max())).title()} |
| Eligible subgroup slices | {len(eligible)} | Minimum 100 observations |
| Eligible recall range | {eligible['recall'].min():.1%} - {eligible['recall'].max():.1%} | Performance variation, not proof of fairness |
| Eligible precision range | {eligible['precision'].min():.1%} - {eligible['precision'].max():.1%} | Review before operational deployment |

## Governance Boundaries

- `duration` is excluded from pre-contact modeling.
- Protected attributes are unavailable, so a complete legal or ethical fairness assessment is impossible.
- PSI compares the model-fit training split with the locked test split; production monitoring should compare a stable reference window with new scored populations.
- Historical associations and feature importance do not establish causality.
"""
    (reports_dir / "model_governance.md").write_text(markdown, encoding="utf-8")
    return governance