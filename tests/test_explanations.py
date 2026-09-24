from catboost import CatBoostRegressor
import pandas as pd
import pytest

from src.explanations import explain_model


def test_native_shap_reconciles_to_saved_model_output(tmp_path):
    features = pd.DataFrame({"hospital_mo": ["A", "B"] * 12, "mean_7": list(range(24))})
    model = CatBoostRegressor(iterations=15, depth=3, verbose=False, allow_writing_files=False)
    model.fit(features, [n / 3 + n % 2 for n in range(24)], cat_features=["hospital_mo"])
    path = tmp_path / "model.cbm"
    model.save_model(str(path))
    loaded = CatBoostRegressor()
    loaded.load_model(str(path))
    result = explain_model(loaded, features.iloc[[20]], ["hospital_mo"])
    assert result["base_value"] + sum(row["contribution"] for row in result["contributions"]) == pytest.approx(result["raw_prediction"])
    assert result["raw_prediction"] == pytest.approx(loaded.predict(features.iloc[[20]])[0])
    assert result["prediction"] == max(0, result["raw_prediction"])
    with pytest.raises(ValueError, match="one profile"):
        explain_model(loaded, features, ["hospital_mo"])
