from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "bank-additional-full.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "campaign_observations.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "outputs" / "predictions" / "propensity_scores.csv"
EVALUATION_SCORES_PATH = PROJECT_ROOT / "outputs" / "predictions" / "locked_test_evaluation_scores.csv"
DATABASE_PATH = PROJECT_ROOT / "outputs" / "bank_marketing_intelligence.sqlite"
MODEL_PATH = PROJECT_ROOT / "models" / "champion_propensity_model.joblib"
METRICS_PATH = PROJECT_ROOT / "outputs" / "reports" / "model_metrics.json"
RANDOM_STATE = 42

EXPECTED_COLUMNS = [
    "age", "job", "marital", "education", "default", "housing", "loan",
    "contact", "month", "day_of_week", "duration", "campaign", "pdays",
    "previous", "poutcome", "emp.var.rate", "cons.price.idx",
    "cons.conf.idx", "euribor3m", "nr.employed", "y",
]

MONTH_ORDER = ["mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
WEEKDAY_ORDER = ["mon", "tue", "wed", "thu", "fri"]


def ensure_directories() -> None:
    for path in [
        PROCESSED_DATA_PATH.parent,
        PREDICTIONS_PATH.parent,
        DATABASE_PATH.parent,
        MODEL_PATH.parent,
        METRICS_PATH.parent,
        PROJECT_ROOT / "outputs" / "dashboard_screenshots",
    ]:
        path.mkdir(parents=True, exist_ok=True)