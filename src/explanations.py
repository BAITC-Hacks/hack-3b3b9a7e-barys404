"""Native CatBoost SHAP contributions for a chosen aggregate referral profile."""
from catboost import Pool
import numpy as np

from src.feature_engineering import CATEGORICAL_FEATURES, make_features
from src.predict import load_model, load_metadata


FEATURE_LABELS = {
    "hospital_mo": "Hospital", "icd10_ref_diag_code": "Referral diagnosis code",
    "bed_profile": "Bed profile", "territorial_type": "Territorial type",
    "referral_purpose": "Referral purpose", "finance_source": "Finance source",
    "registration_day_of_week": "Registration weekday", "registration_day": "Day of month",
    "registration_month": "Registration month", "horizon": "Forecast horizon",
    "target_day_of_week": "Target weekday", "lag_1": "Last observed day",
    "lag_7": "Observed count six days before origin", "lag_14": "Observed count thirteen days before origin",
    "mean_7": "Observed 7-day mean", "mean_14": "Observed 14-day mean", "mean_28": "Observed 28-day mean",
}


def explain_model(model, features, categorical):
    """SHAP contributions sum to the raw output; clipping is recorded separately."""
    if len(features) != 1:
        raise ValueError("Explain one profile at a time.")
    values = np.asarray(model.get_feature_importance(
        Pool(features, cat_features=categorical), type="ShapValues"), dtype=float)[0]
    raw = float(model.predict(features)[0])
    if not np.isfinite(values).all() or not np.isfinite(raw):
        raise ValueError("Explanation contains non-finite values.")
    if not np.isclose(values.sum(), raw, atol=1e-7):
        raise ValueError("Explanation does not reconcile with the model prediction.")
    contributions = [{"feature": name, "label": FEATURE_LABELS.get(name, name), "contribution": float(value)}
                     for name, value in zip(features.columns, values[:-1])]
    return {"base_value": float(values[-1]), "raw_prediction": raw, "prediction": max(0., raw),
            "clipping_adjustment": max(0., raw) - raw,
            "contributions": sorted(contributions, key=lambda row: abs(row["contribution"]), reverse=True),
            "method": "CatBoost SHAP; model associations, not causal effects"}


def explain_waiting(record):
    features = make_features(record)
    metadata = load_metadata()
    result = explain_model(load_model(), features, CATEGORICAL_FEATURES)
    result["unseen_categories"] = [name for name in CATEGORICAL_FEATURES
                                   if features.iloc[0][name] not in metadata.get("feature_options", {}).get(name, [])]
    return result
