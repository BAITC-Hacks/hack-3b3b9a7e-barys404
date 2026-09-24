import numpy as np
import pandas as pd
import pytest

from src.validation import waiting_fold, error_groups, pooled_metrics


def test_fold_purges_unavailable_outcomes_and_excludes_other_test_windows():
    frame = pd.DataFrame({
        "registration_dt": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-02-01", "2025-02-14 23:59", "2025-02-15", "2025-02-02"], format="mixed"),
        "hospitalization_dt": pd.to_datetime(["2025-01-02", "2025-02-01", "2025-02-20", "2025-03-01", "2025-03-01", "2025-02-03"]),
        "refusal_dt": pd.to_datetime([None, None, None, None, None, "2025-02-02"]),
        "wait_days": [1, 30, 19, 15, 14, 1], "target_eligible": True,
    })
    train, test, purged = waiting_fold(frame, "2025-02-01", "2025-02-14")
    assert train.index.tolist() == [0]
    assert test.index.tolist() == [2, 3]
    assert purged == 1
    changed = frame.copy()
    changed.loc[2:, "wait_days"] = 70
    new_train, _, _ = waiting_fold(changed, "2025-02-01", "2025-02-14")
    pd.testing.assert_frame_equal(train, new_train)


def test_group_suppression_and_metrics_are_observation_weighted():
    scored = pd.DataFrame({"region": ["A", "A", "B"], "actual": [0., 4., 100.],
                           "prediction": [1., 2., 90.], "baseline": [0., 0., 0.]})
    groups = error_groups(scored, "region", minimum=2)
    assert len(groups) == 1 and groups[0]["region"] == "A"
    assert groups[0]["mae"] == 1.5
    assert pooled_metrics(scored)["mae"] == pytest.approx(13 / 3)
    assert pooled_metrics(scored)["rmse"] == pytest.approx(np.sqrt(105 / 3))
    with pytest.raises(ValueError):
        error_groups(scored, "region", minimum=1)
