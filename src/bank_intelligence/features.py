from __future__ import annotations

import numpy as np
import pandas as pd

from .config import MONTH_ORDER, WEEKDAY_ORDER


EDUCATION_MAP = {
    "illiterate": "foundational",
    "basic.4y": "foundational",
    "basic.6y": "foundational",
    "basic.9y": "foundational",
    "high.school": "secondary",
    "professional.course": "professional",
    "university.degree": "tertiary",
    "unknown": "unknown",
}


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["conversion_flag"] = result["y"].eq("yes").astype("int8")
    result["age_band"] = pd.cut(
        result["age"], bins=[-np.inf, 29, 39, 49, 59, np.inf],
        labels=["17-29", "30-39", "40-49", "50-59", "60+"], right=True,
    ).astype(str)
    result["previously_contacted_flag"] = result["previous"].gt(0).astype("int8")
    result["previous_campaign_success_flag"] = result["poutcome"].eq("success").astype("int8")
    result["campaign_contact_band"] = pd.cut(
        result["campaign"], bins=[0, 1, 2, 4, np.inf],
        labels=["1 contact", "2 contacts", "3-4 contacts", "5+ contacts"],
    ).astype(str)
    result["total_recorded_contacts"] = result["campaign"] + result["previous"]
    result["contact_intensity_band"] = pd.cut(
        result["total_recorded_contacts"], bins=[-1, 1, 3, 6, np.inf],
        labels=["low", "moderate", "high", "very high"],
    ).astype(str)
    result["housing_loan_profile"] = result["housing"].map(
        {"yes": "housing loan", "no": "no housing loan", "unknown": "unknown"}
    )
    result["personal_loan_profile"] = result["loan"].map(
        {"yes": "personal loan", "no": "no personal loan", "unknown": "unknown"}
    )
    housing_is_yes = result["housing"].eq("yes").to_numpy(dtype=bool)
    loan_is_yes = result["loan"].eq("yes").to_numpy(dtype=bool)
    default_is_unknown = result["default"].eq("unknown").to_numpy(dtype=bool)
    housing_is_unknown = result["housing"].eq("unknown").to_numpy(dtype=bool)
    loan_is_unknown = result["loan"].eq("unknown").to_numpy(dtype=bool)
    credit_conditions = [
        result["default"].eq("yes").to_numpy(dtype=bool),
        housing_is_yes & loan_is_yes,
        housing_is_yes | loan_is_yes,
        default_is_unknown | housing_is_unknown | loan_is_unknown,
    ]
    result["credit_exposure_profile"] = np.select(
        credit_conditions,
        ["credit default reported", "housing + personal loan", "single loan exposure", "exposure unknown"],
        default="no reported loan exposure",
    )
    result["education_group"] = result["education"].map(EDUCATION_MAP).fillna("other")
    result["macroeconomic_regime"] = np.select(
        [
            result["emp.var.rate"].lt(0) & result["euribor3m"].lt(2),
            result["emp.var.rate"].lt(0) & result["euribor3m"].ge(2),
            result["emp.var.rate"].ge(0) & result["euribor3m"].lt(2),
        ],
        ["contraction / low rate", "contraction / elevated rate", "expansion / low rate"],
        default="expansion / high rate",
    )
    month_sort_map = {value: index + 1 for index, value in enumerate(MONTH_ORDER)}
    weekday_sort_map = {value: index + 1 for index, value in enumerate(WEEKDAY_ORDER)}
    result["month_sort"] = result["month"].map(month_sort_map).astype("int8")
    result["weekday_sort"] = result["day_of_week"].map(weekday_sort_map).astype("int8")
    result["customer_profile_segment"] = np.select(
        [
            result["poutcome"].eq("success"),
            result["job"].isin(["student", "retired"]) & result["age"].ge(60),
            result["job"].eq("student"),
            result["credit_exposure_profile"].eq("no reported loan exposure"),
            result["previously_contacted_flag"].eq(1),
        ],
        [
            "previous campaign success", "retired senior", "early-career student",
            "no reported loan exposure", "previously contacted",
        ],
        default="general profile",
    )
    if result.isna().any().any():
        missing = result.columns[result.isna().any()].tolist()
        raise ValueError(f"Feature engineering introduced nulls: {missing}")
    return result