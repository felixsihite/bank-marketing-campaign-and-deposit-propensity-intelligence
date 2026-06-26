from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import RANDOM_STATE


NUMERIC_FEATURES = [
    "age", "campaign", "pdays", "previous", "emp.var.rate", "cons.price.idx",
    "cons.conf.idx", "euribor3m", "nr.employed", "total_recorded_contacts",
]
CATEGORICAL_FEATURES = [
    "job", "marital", "education", "default", "housing", "loan", "contact",
    "month", "day_of_week", "poutcome", "age_band", "campaign_contact_band",
    "contact_intensity_band", "credit_exposure_profile", "education_group",
    "macroeconomic_regime", "customer_profile_segment",
]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric, NUMERIC_FEATURES),
        ("categorical", categorical, CATEGORICAL_FEATURES),
    ], verbose_feature_names_out=True)


def model_registry() -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline([
            ("preprocessor", _preprocessor()),
            ("model", LogisticRegression(max_iter=1200, class_weight="balanced", random_state=RANDOM_STATE)),
        ]),
        "random_forest": Pipeline([
            ("preprocessor", _preprocessor()),
            ("model", RandomForestClassifier(
                n_estimators=160, max_depth=14, min_samples_leaf=5,
                class_weight="balanced_subsample", random_state=RANDOM_STATE, n_jobs=-1,
            )),
        ]),
        "gradient_boosting": Pipeline([
            ("preprocessor", _preprocessor()),
            ("model", GradientBoostingClassifier(
                n_estimators=120, learning_rate=0.05, max_depth=3,
                subsample=0.85, random_state=RANDOM_STATE,
            )),
        ]),
    }


def _metric_dict(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predictions)
    return {
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "threshold": float(threshold),
        "confusion_matrix": matrix.tolist(),
    }


def _recommended_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    beta_squared = 4.0
    scores = (1 + beta_squared) * precision[:-1] * recall[:-1] / (
        beta_squared * precision[:-1] + recall[:-1] + 1e-12
    )
    return float(thresholds[int(np.nanargmax(scores))])


def _feature_importance(fitted_pipeline: Pipeline) -> pd.DataFrame:
    names = fitted_pipeline.named_steps["preprocessor"].get_feature_names_out()
    model = fitted_pipeline.named_steps["model"]
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
        direction = np.repeat("magnitude", len(values))
    else:
        coefficients = model.coef_[0]
        values = np.abs(coefficients)
        direction = np.where(coefficients >= 0, "positive", "negative")
    table = pd.DataFrame({"feature": names, "importance": values, "direction": direction})
    table["feature"] = table["feature"].str.replace("numeric__", "", regex=False).str.replace("categorical__", "", regex=False)
    return table.sort_values("importance", ascending=False).head(30).reset_index(drop=True)


def train_and_score(
    frame: pd.DataFrame,
    model_path: Path,
    metrics_path: Path,
    predictions_path: Path,
    reports_dir: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    X = pd.DataFrame(frame.loc[:, MODEL_FEATURES])
    y = frame["conversion_flag"].astype(int)
    train_val_idx, test_idx = train_test_split(
        frame.index, test_size=0.20, stratify=y, random_state=RANDOM_STATE,
    )
    train_idx, validation_idx = train_test_split(
        train_val_idx, test_size=0.25, stratify=y.loc[train_val_idx], random_state=RANDOM_STATE,
    )
    X_train, y_train = X.loc[train_idx], y.loc[train_idx]
    X_validation, y_validation = X.loc[validation_idx], y.loc[validation_idx]
    X_test, y_test = X.loc[test_idx], y.loc[test_idx]

    scoring = {"pr_auc": "average_precision", "roc_auc": "roc_auc", "f1": "f1"}
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    candidates: dict[str, Any] = {}
    fitted_candidates: dict[str, Pipeline] = {}
    for name, pipeline in model_registry().items():
        cv_result = cross_validate(pipeline, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1)
        fitted = clone(pipeline).fit(X_train, y_train)
        validation_probability = fitted.predict_proba(X_validation)[:, 1]
        candidates[name] = {
            "cv_pr_auc_mean": float(cv_result["test_pr_auc"].mean()),
            "cv_pr_auc_std": float(cv_result["test_pr_auc"].std()),
            "cv_roc_auc_mean": float(cv_result["test_roc_auc"].mean()),
            "cv_f1_mean": float(cv_result["test_f1"].mean()),
            "validation_pr_auc": float(average_precision_score(y_validation, validation_probability)),
            "validation_roc_auc": float(roc_auc_score(y_validation, validation_probability)),
        }
        fitted_candidates[name] = fitted

    champion_name = max(candidates, key=lambda key: candidates[key]["validation_pr_auc"])
    champion_base = model_registry()[champion_name]
    calibrated = CalibratedClassifierCV(champion_base, method="sigmoid", cv=3)
    calibrated.fit(X_train, y_train)
    validation_probability = calibrated.predict_proba(X_validation)[:, 1]
    threshold = _recommended_threshold(y_validation, validation_probability)
    test_probability = calibrated.predict_proba(X_test)[:, 1]
    test_metrics = _metric_dict(y_test, test_probability, threshold)

    test_evaluation = frame.loc[test_idx, ["campaign_record_id"]].copy()
    test_evaluation["conversion_flag"] = y_test.to_numpy()
    test_evaluation["evaluation_probability"] = test_probability
    test_evaluation["predicted_positive_flag"] = (test_probability >= threshold).astype("int8")
    test_rank = test_evaluation["evaluation_probability"].rank(method="first", ascending=False)
    test_evaluation["locked_test_decile"] = pd.qcut(
        test_rank, 10, labels=range(1, 11),
    ).astype(int)
    locked_test_deciles = (
        test_evaluation.groupby("locked_test_decile", observed=True)["conversion_flag"]
        .agg(observations="size", subscriptions="sum", conversion_rate="mean")
        .reset_index()
        .sort_values("locked_test_decile")
    )
    evaluation_path = predictions_path.parent / "locked_test_evaluation_scores.csv"
    test_evaluation.to_csv(evaluation_path, index=False)
    locked_test_deciles.to_csv(reports_dir / "locked_test_decile_performance.csv", index=False)
    powerbi_dir = reports_dir.parents[1] / "data" / "processed" / "powerbi"
    powerbi_dir.mkdir(parents=True, exist_ok=True)
    locked_test_deciles.to_csv(powerbi_dir / "model_evaluation_decile.csv", index=False)

    probability_true, probability_pred = calibration_curve(
        y_test, test_probability, n_bins=10, strategy="quantile",
    )
    test_metrics["calibration_curve"] = {
        "mean_predicted_probability": probability_pred.tolist(),
        "observed_positive_rate": probability_true.tolist(),
    }

    importance = _feature_importance(fitted_candidates[champion_name])
    importance.to_csv(reports_dir / "feature_importance.csv", index=False)

    final_model = CalibratedClassifierCV(model_registry()[champion_name], method="sigmoid", cv=3)
    final_model.fit(X.loc[train_val_idx], y.loc[train_val_idx])
    all_probabilities = final_model.predict_proba(X)[:, 1]
    scored = pd.DataFrame(frame.loc[:, ["campaign_record_id", "conversion_flag"]]).copy()
    scored["data_split"] = "model_fit_train"
    scored.loc[validation_idx, "data_split"] = "model_fit_validation"
    scored.loc[test_idx, "data_split"] = "locked_test"
    scored["propensity_score"] = all_probabilities
    score_rank = scored["propensity_score"].rank(method="first", ascending=False)
    scored["propensity_decile"] = pd.qcut(score_rank, 10, labels=range(1, 11)).astype(int)
    scored["recommended_contact_flag"] = scored["propensity_score"].ge(threshold).astype("int8")
    scored["priority_tier"] = np.select(
        [
            scored["propensity_decile"].eq(1),
            scored["propensity_decile"].le(3),
            scored["propensity_decile"].le(5),
        ],
        ["very high", "high", "consider"],
        default="monitor",
    )
    scored.to_csv(predictions_path, index=False)

    top_decile_rate = float(locked_test_deciles.loc[
        locked_test_deciles["locked_test_decile"].eq(1), "conversion_rate"
    ].iloc[0])
    overall_rate = float(y_test.mean())
    metrics: dict[str, Any] = {
        "modeling_policy": {
            "target": "term-deposit subscription (y)",
            "duration_excluded": True,
            "reason": "Call duration is unavailable before contact and would cause target leakage.",
            "random_state": RANDOM_STATE,
            "split": "60% train / 20% validation / 20% locked test",
        },
        "candidate_models": candidates,
        "champion_model": champion_name,
        "threshold_strategy": "Validation-set maximum F2 score (recall weighted 2x)",
        "recommended_threshold": threshold,
        "test_metrics": test_metrics,
        "portfolio_scoring_note": "Final scores use a model refit on train+validation; locked test metrics remain the unbiased performance estimate.",
        "decile_reporting_policy": "Model evaluation charts and lift use locked_test_decile_performance only. Full-portfolio scores are operational ranking outputs, not unbiased evaluation.",
        "locked_test_observation_count": int(len(test_evaluation)),
        "locked_test_decile_performance": locked_test_deciles.to_dict(orient="records"),
        "high_propensity_observation_count": int(scored["recommended_contact_flag"].sum()),
        "top_decile_conversion_rate": top_decile_rate,
        "top_decile_lift": top_decile_rate / overall_rate,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    joblib.dump(final_model, model_path)
    return scored, metrics