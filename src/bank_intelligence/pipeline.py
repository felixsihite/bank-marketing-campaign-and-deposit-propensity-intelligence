from __future__ import annotations

import json
import os
from dataclasses import asdict

from .analytics import build_analytics
from .config import (
    DATABASE_PATH, EVALUATION_SCORES_PATH, METRICS_PATH, MODEL_PATH, PREDICTIONS_PATH, PROCESSED_DATA_PATH,
    PROJECT_ROOT, RAW_DATA_PATH, ensure_directories,
)
from .data import load_raw, standardize_source, validate_source
from .database import build_database, validate_database
from .features import build_features
from .governance import generate_governance_reports
from .modeling import train_and_score
from .reporting import create_dashboard_pages, write_reports


def run() -> dict:
    ensure_directories()
    reports_dir = PROJECT_ROOT / "outputs" / "reports"
    raw = load_raw(RAW_DATA_PATH)
    audit = validate_source(raw, RAW_DATA_PATH)
    processed = build_features(standardize_source(raw))
    processed.to_csv(PROCESSED_DATA_PATH, index=False)
    build_analytics(processed, PROJECT_ROOT / "outputs" / "analysis")
    reuse_model_outputs = (
        os.getenv("BANK_INTELLIGENCE_REUSE_MODEL_OUTPUTS") == "1"
        and MODEL_PATH.exists() and METRICS_PATH.exists() and PREDICTIONS_PATH.exists()
        and EVALUATION_SCORES_PATH.exists()
    )
    if reuse_model_outputs:
        import pandas as pd
        scored = pd.read_csv(PREDICTIONS_PATH)
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    else:
        scored, metrics = train_and_score(
            processed, MODEL_PATH, METRICS_PATH, PREDICTIONS_PATH, reports_dir,
        )
    governance = generate_governance_reports(
        processed, scored, EVALUATION_SCORES_PATH, metrics, reports_dir,
    )
    build_database(
        processed,
        scored,
        DATABASE_PATH,
        PROJECT_ROOT / "sql" / "ddl" / "01_schema.sql",
        PROJECT_ROOT / "sql" / "transformations" / "02_star_schema_load.sql",
        PROJECT_ROOT / "sql" / "marts" / "03_business_marts.sql",
    )
    database_counts = validate_database(DATABASE_PATH)
    if database_counts["fact_campaign_contact"] != len(raw):
        raise RuntimeError("Fact table row count failed source reconciliation")
    write_reports(processed, audit, metrics, database_counts, reports_dir)
    create_dashboard_pages(
        processed,
        scored,
        metrics,
        reports_dir / "feature_importance.csv",
        PROJECT_ROOT / "outputs" / "dashboard_screenshots",
    )
    manifest = {
        "project": "Bank Marketing Campaign & Deposit Propensity Intelligence",
        "source": str(RAW_DATA_PATH.relative_to(PROJECT_ROOT)),
        "source_sha256": audit.source_sha256,
        "quality_audit": asdict(audit),
        "database_counts": database_counts,
        "champion_model": metrics["champion_model"],
        "test_metrics": metrics["test_metrics"],
        "governance": governance,
    }
    (PROJECT_ROOT / "outputs" / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))