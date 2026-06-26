import json

import pandas as pd

from bank_intelligence.config import EVALUATION_SCORES_PATH, METRICS_PATH, PROJECT_ROOT


def test_locked_test_decile_contract():
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    evaluation = pd.read_csv(EVALUATION_SCORES_PATH)
    deciles = pd.read_csv(PROJECT_ROOT / "outputs" / "reports" / "locked_test_decile_performance.csv")

    assert len(evaluation) == metrics["locked_test_observation_count"] == 8238
    assert evaluation["campaign_record_id"].is_unique
    assert evaluation["locked_test_decile"].nunique() == 10
    assert len(deciles) == 10
    assert deciles["observations"].sum() == len(evaluation)
    assert deciles["subscriptions"].sum() == evaluation["conversion_flag"].sum() == 928
    top_rate = deciles.loc[deciles["locked_test_decile"].eq(1), "conversion_rate"].iloc[0]
    assert abs(top_rate - metrics["top_decile_conversion_rate"]) < 1e-12
    assert "locked_test" in metrics["decile_reporting_policy"]


def test_operational_scores_are_labeled_separately():
    scores = pd.read_csv(PROJECT_ROOT / "outputs" / "predictions" / "propensity_scores.csv")
    assert set(scores["data_split"].unique()) == {
        "model_fit_train", "model_fit_validation", "locked_test",
    }
    assert scores["propensity_score"].between(0, 1).all()
    assert scores["propensity_decile"].between(1, 10).all()