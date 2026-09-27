"""Native CatBoost SHAP contributions for a chosen aggregate referral profile."""
from catboost import Pool
import numpy as np

from ml.feature_engineering import CATEGORICAL_FEATURES, make_features
from ml.predict import load_model, load_metadata
from ml.waiting_estimator import calibrated_predictions


FEATURE_LABELS = {
  "hospital_mo": "Стационар",
  "icd10_ref_diag_code": "Код диагноза направления",
  "bed_profile": "Профиль койки",
  "territorial_type": "Территориальный тип",
  "referral_purpose": "Цель направления",
  "finance_source": "Источник финансирования",
  "registration_day_of_week": "День недели регистрации",
  "registration_day": "День месяца",
  "registration_month": "Месяц регистрации",
  "horizon": "День горизонта",
  "target_day_of_week": "День недели прогноза",
  "lag_1": "Последний наблюдённый день",
  "lag_7": "За 6 дней до начала прогноза",
  "lag_14": "За 13 дней до начала прогноза",
  "mean_7": "Среднее за 7 дней",
  "mean_14": "Среднее за 14 дней",
  "mean_28": "Среднее за 28 дней"
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
    model = load_model()
    raw = float(model.predict(features)[0])
    prediction, methods, support = calibrated_predictions(features, [raw], metadata.get("calibration"))
    method = str(methods[0])
    if method == "catboost":
        result = explain_model(model, features, CATEGORICAL_FEATURES)
    else:
        value = float(prediction[0])
        result = {"prediction": value, "raw_prediction": value, "base_value": value,
                  "clipping_adjustment": 0., "contributions": []}
    result.update(method=method, support=int(support[0]),
                  catboost_raw_prediction=raw,
                  training_cutoff=metadata.get("split", {}).get("test_start", "")[:10])
    result["unseen_categories"] = [name for name in CATEGORICAL_FEATURES
                                   if features.iloc[0][name] not in metadata.get("feature_options", {}).get(name, [])]
    return result
