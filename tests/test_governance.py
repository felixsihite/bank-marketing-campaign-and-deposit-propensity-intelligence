import json

import pandas as pd

from bank_intelligence.config import PROJECT_ROOT
from bank_intelligence.governance import categorical_psi, numeric_psi


def test_psi_functions_detect_stability_and_shift():
    baseline = pd.Series(range(1, 101))
    assert numeric_psi(baseline, baseline) < 1e-10
    assert numeric_psi(baseline, baseline + 100) >= 0.25

    categories = pd.Series(["a"] * 70 + ["b"] * 30)
    shifted = pd.Series(["a"] * 20 + ["b"] * 80)
    assert categorical_psi(categories, categories) < 1e-10
    assert categorical_psi(categories, shifted) >= 0.10


def test_governance_outputs_are_complete():
    reports = PROJECT_ROOT / "outputs" / "reports"
    governance = json.loads((reports / "model_governance.json").read_text(encoding="utf-8"))
    drift = pd.read_csv(reports / "drift_monitoring.csv")
    subgroup = pd.read_csv(reports / "subgroup_performance.csv")

    assert governance["locked_test_observations"] == 8238
    assert 0 <= governance["expected_calibration_error"] <= 1
    assert governance["drift_status"] in {"stable", "moderate", "high"}
    assert {"feature", "psi", "status"}.issubset(drift.columns)
    assert not drift[["feature", "psi", "status"]].isna().any().any()
    assert {"dimension", "member", "observations", "precision", "recall"}.issubset(subgroup.columns)
    assert not subgroup.empty
    assert subgroup["precision"].between(0, 1).all()
    assert subgroup["recall"].between(0, 1).all()