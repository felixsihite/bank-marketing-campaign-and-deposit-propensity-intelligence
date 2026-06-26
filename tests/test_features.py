from bank_intelligence.config import RAW_DATA_PATH
from bank_intelligence.data import load_raw, standardize_source
from bank_intelligence.features import build_features
from bank_intelligence.modeling import MODEL_FEATURES


def test_feature_contract_has_no_nulls_and_no_duration_leakage():
    featured = build_features(standardize_source(load_raw(RAW_DATA_PATH)))
    assert len(featured) == 41188
    assert not featured.isna().any().any()
    assert featured["conversion_flag"].sum() == 4640
    assert "duration" not in MODEL_FEATURES
    assert featured["campaign_record_id"].is_unique