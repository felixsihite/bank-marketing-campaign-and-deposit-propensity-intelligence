from bank_intelligence.config import RAW_DATA_PATH
from bank_intelligence.data import load_raw, validate_source


def test_source_contract_and_integrity():
    frame = load_raw(RAW_DATA_PATH)
    audit = validate_source(frame, RAW_DATA_PATH)
    assert (audit.row_count, audit.column_count) == (41188, 21)
    assert audit.native_null_cells == 0
    assert audit.exact_duplicate_rows == 12
    assert audit.positive_observations == 4640
    assert audit.pdays_999_count == 39673