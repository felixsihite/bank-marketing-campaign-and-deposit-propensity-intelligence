from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import EXPECTED_COLUMNS


@dataclass(frozen=True)
class QualityAudit:
    row_count: int
    column_count: int
    native_null_cells: int
    exact_duplicate_rows: int
    positive_observations: int
    positive_rate: float
    pdays_999_count: int
    unknown_counts: dict[str, int]
    numeric_ranges: dict[str, dict[str, float]]
    source_sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_raw(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";", quotechar='"')
    frame.columns = [column.strip() for column in frame.columns]
    return frame


def validate_source(frame: pd.DataFrame, source_path: Path) -> QualityAudit:
    if list(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Schema mismatch. Expected {EXPECTED_COLUMNS}, found {list(frame.columns)}")
    if frame.shape != (41188, 21):
        raise ValueError(f"Unexpected source shape: {frame.shape}; expected (41188, 21)")
    if bool(frame.isna().to_numpy().any()):
        raise ValueError("Native null cells detected; source is expected to contain none")
    if not bool(frame["y"].isin(["yes", "no"]).to_numpy(dtype=bool).all()):
        raise ValueError("Target contains values outside {'yes', 'no'}")

    numeric_rules = {
        "age": (17, 100), "duration": (0, np.inf), "campaign": (1, np.inf),
        "pdays": (0, 999), "previous": (0, np.inf),
        "emp.var.rate": (-10, 10), "cons.price.idx": (80, 110),
        "cons.conf.idx": (-100, 10), "euribor3m": (0, 20),
        "nr.employed": (4000, 6000),
    }
    for column, (minimum, maximum) in numeric_rules.items():
        is_valid_range = frame[column].between(minimum, maximum).to_numpy(dtype=bool).all()
        if not bool(is_valid_range):
            raise ValueError(f"Numeric range validation failed for {column}")

    categorical = frame.select_dtypes(include="object").columns
    unknown_counts: dict[str, int] = {}
    for column in categorical:
        unknown_mask = frame[column].eq("unknown")
        if bool(unknown_mask.to_numpy(dtype=bool).any()):
            unknown_counts[str(column)] = int(unknown_mask.sum())
    numeric_ranges = {
        column: {"min": float(frame[column].min()), "max": float(frame[column].max())}
        for column in frame.select_dtypes(include=np.number).columns
    }
    positive = int(frame["y"].eq("yes").sum())
    return QualityAudit(
        row_count=len(frame),
        column_count=frame.shape[1],
        native_null_cells=int(frame.isna().sum().sum()),
        exact_duplicate_rows=int(frame.duplicated().sum()),
        positive_observations=positive,
        positive_rate=positive / len(frame),
        pdays_999_count=int(frame["pdays"].eq(999).sum()),
        unknown_counts=unknown_counts,
        numeric_ranges=numeric_ranges,
        source_sha256=sha256_file(source_path),
    )


def standardize_source(frame: pd.DataFrame) -> pd.DataFrame:
    clean = frame.copy()
    object_columns = clean.select_dtypes(include="object").columns
    clean[object_columns] = clean[object_columns].apply(lambda series: series.str.strip().str.lower())
    clean.insert(0, "campaign_record_id", np.arange(1, len(clean) + 1, dtype="int64"))
    clean.insert(1, "source_row_number", np.arange(2, len(clean) + 2, dtype="int64"))
    duplicate_mask = frame.duplicated(keep=False)
    clean["exact_duplicate_group_flag"] = duplicate_mask.astype("int8")
    clean["exact_duplicate_excess_flag"] = frame.duplicated(keep="first").astype("int8")
    return clean