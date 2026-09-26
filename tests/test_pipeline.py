"""Isolated CSV-to-Parquet tests for data integrity at the integration boundary."""
import csv
from datetime import datetime

import duckdb
import pytest

from backend.data_pipeline import preprocessing
from backend.data_pipeline.data_loader import coverage, load_raw_table
from backend.data_pipeline.data_quality import inspect_table


WAITING = {
    "region_origin_code": "01", "mo_destination_code": "0007", "profile_code": "003",
    "patient_seq_no": "0009", "icd10_ref_diag_code": "J01", "diagnosis_name": "Example",
    "registration_dt": "2025-01-01 12:30:00", "planned_dt": "2025-01-01 00:00:00",
    "sdu_load_date": "2025-04-01",
}
REFERRAL = {
    "hospitalization_code": "01.0007.003.0009", "hospital_mo": "Hospital A",
    "bed_profile": "Profile", "icd10_ref_diag_code": "J01", "diagnosis_name": "Example",
    "registration_dt": "2025-01-01 12:30:00", "planned_dt": "2025-01-01 00:00:00",
    "hospitalization_dt": "2025-01-03 12:30:00", "refusal_dt": "", "sdu_load_date": "2025-04-01",
}


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    # Every export and DuckDB table is isolated from the real-data pipeline.
    monkeypatch.setattr(preprocessing, "PROCESSED_DIR", tmp_path)
    with duckdb.connect(":memory:") as connection:
        yield connection, tmp_path


def _csv(path, defaults, changes):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(defaults))
        writer.writeheader()
        writer.writerows({**defaults, **row} for row in changes)
    return path


def _prepare(pipeline, waiting_changes=None, referral_parts=None):
    connection, directory = pipeline
    waiting_path = _csv(directory / "waiting.csv", WAITING, waiting_changes or [{}])
    referral_paths = [
        _csv(directory / f"referrals_part_{index:03d}_of_003.csv", REFERRAL, records)
        for index, records in enumerate(referral_parts or [[{}]], start=1)
    ]
    report = {"datasets": {}, "cleaning": {}}
    for category, paths in (("waiting", [waiting_path]), ("referrals", referral_paths)):
        columns = load_raw_table(connection, category, paths)
        report["datasets"][category] = inspect_table(connection, category, columns)
        preprocessing.clean_dates(connection, category, columns)
    return report


def test_coverage_recognizes_cyrillic_part_names(tmp_path):
    files = {
        "waiting": [tmp_path / "Ожидающие.csv"],
        "referrals": [
            tmp_path / f"Направления Часть {part} из 3.csv" for part in range(1, 4)
        ],
        "refusals": [
            tmp_path / f"Отказы Часть {part} из 6.csv" for part in range(1, 7)
        ],
        "treated": [],
    }

    result = coverage(files)

    assert result["referrals"]["available_parts"] == [1, 2, 3]
    assert result["referrals"]["complete"] is True
    assert result["refusals"]["available_parts"] == [1, 2, 3, 4, 5, 6]
    assert result["refusals"]["complete"] is True


def test_composite_codes_preserve_leading_zeros_through_csv_join(pipeline):
    connection, directory = pipeline
    report = _prepare(pipeline)
    assert connection.execute("SELECT hospitalization_code_generated FROM clean_waiting").fetchone()[0] == "01.0007.003.0009"
    preprocessing.create_analytical(connection, report)
    assert report["join"]["match_rate"] == 1.0
    assert connection.execute("SELECT region_origin_code, mo_destination_code, profile_code, waiting_key_matched FROM analytical").fetchone() == ("01", "0007", "003", True)
    assert (directory / "analytical.parquet").exists()


def test_date_sentinels_are_reported_and_same_day_midnight_plans_remain_valid(pipeline):
    connection, _ = pipeline
    report = _prepare(pipeline, waiting_changes=[
        {"patient_seq_no": "1", "planned_dt": "1900-01-01"},
        {"patient_seq_no": "2", "planned_dt": "1970-01-01"},
        {"patient_seq_no": "3", "planned_dt": "broken date"},
        {"patient_seq_no": "4", "planned_dt": "2025-01-01 00:00:00"},
        {"patient_seq_no": "5", "planned_dt": "2099-01-01"},
    ])
    planned_quality = report["datasets"]["waiting"]["dates"]["planned_dt"]
    assert planned_quality["out_of_range"] == 3
    assert planned_quality["parse_invalid"] == 1
    assert planned_quality["before_registration"] == 2
    assert connection.execute("SELECT count(*) FROM clean_waiting WHERE planned_dt IS NULL").fetchone()[0] == 4
    assert connection.execute("SELECT planned_dt FROM clean_waiting WHERE patient_seq_no='4'").fetchone()[0] == datetime(2025, 1, 1)
    assert connection.execute("SELECT planned_dt FROM clean_referrals").fetchone()[0] == datetime(2025, 1, 1)


@pytest.mark.parametrize("bad_hospitalization", ["2024-12-31", "1900-01-01", "not a date", "2099-01-01"])
def test_invalid_hospitalization_does_not_become_an_unresolved_queue_record(pipeline, bad_hospitalization):
    connection, _ = pipeline
    report = _prepare(pipeline, referral_parts=[[{"hospitalization_dt": bad_hospitalization}]])
    # The original nonempty outcome must be retained even after date cleanup.
    assert connection.execute("SELECT hospitalization_dt, had_hospitalization FROM clean_referrals").fetchone() == (None, True)
    preprocessing.create_analytical(connection, report)
    assert connection.execute("SELECT outcome, target_eligible, queue_reconstruction_eligible FROM analytical").fetchone() == ("invalid_outcome", False, False)
    assert report["cleaning"]["target_excluded"] == 1


def test_overlapping_parts_do_not_inflate_referrals_or_join(pipeline):
    connection, _ = pipeline
    report = _prepare(pipeline, referral_parts=[[{}], [{"sdu_load_date": "2025-05-01"}]])
    preprocessing.create_analytical(connection, report)
    assert report["datasets"]["referrals"]["rows"] == 2
    assert report["cleaning"]["referrals_exact_duplicates_removed"] == 1
    assert report["summary"]["referral_records"] == 1
    assert report["join"]["analytical_rows"] == 1
    assert report["join"]["matched_rows"] == 2
    assert report["join"]["match_rate"] == 1.0


def test_conflicting_referral_key_is_quarantined_and_never_many_to_many_joined(pipeline):
    connection, directory = pipeline
    report = _prepare(pipeline, referral_parts=[[
        {},
        {"hospitalization_dt": "2025-01-04 12:30:00"},
        {"hospitalization_code": "01.0007.003.0010"},
    ]])
    preprocessing.create_analytical(connection, report)
    assert report["cleaning"]["referrals_conflicting_key_rows_excluded"] == 2
    assert report["join"]["referral_conflicting_keys"] == 1
    assert report["summary"]["referral_records"] == 1
    assert connection.execute("SELECT hospitalization_code FROM analytical").fetchone()[0] == "01.0007.003.0010"
    assert connection.execute("SELECT count(*) FROM read_parquet(?)", [str(directory / "referral_key_quarantine.parquet")]).fetchone()[0] == 2


def test_ambiguous_waiting_key_does_not_duplicate_referral_or_invent_region(pipeline):
    connection, _ = pipeline
    report = _prepare(pipeline, waiting_changes=[{}, {"diagnosis_name": "Conflicting description"}])
    preprocessing.create_analytical(connection, report)
    assert report["join"]["waiting_ambiguous_keys"] == 1
    assert report["join"]["analytical_rows"] == 1
    assert report["join"]["matched_rows"] == 1
    assert report["join"]["unambiguous_matched_rows"] == 0
    assert connection.execute("SELECT waiting_key_matched, region_origin_code FROM analytical").fetchone() == (False, None)


def test_conflicting_outcomes_and_missing_key_are_explicitly_accounted_for(pipeline):
    connection, _ = pipeline
    report = _prepare(pipeline, referral_parts=[[
        {"refusal_dt": "2025-01-02 12:30:00"},
        {"hospitalization_code": ""},
    ]])
    preprocessing.create_analytical(connection, report)
    assert report["cleaning"]["referrals_missing_key_excluded"] == 1
    assert report["summary"]["conflicting"] == 1
    assert connection.execute("SELECT target_eligible, queue_reconstruction_eligible FROM analytical").fetchone() == (False, False)


def test_distinct_invalid_referral_dates_remain_conflicting_source_records(pipeline):
    connection, _ = pipeline
    report = _prepare(pipeline, referral_parts=[[
        {"hospitalization_dt": "1900-01-01"},
        {"hospitalization_dt": "1970-01-01"},
    ]])
    assert connection.execute("SELECT count(*) FROM clean_referrals WHERE hospitalization_dt IS NULL").fetchone()[0] == 2
    preprocessing.create_analytical(connection, report)
    assert report["cleaning"]["referrals_exact_duplicates_removed"] == 0
    assert report["cleaning"]["referrals_conflicting_key_rows_excluded"] == 2
    assert report["join"]["referral_conflicting_keys"] == 1
    assert report["summary"]["referral_records"] == 0


def test_distinct_invalid_waiting_dates_preserve_join_ambiguity(pipeline):
    connection, _ = pipeline
    report = _prepare(pipeline, waiting_changes=[
        {"planned_dt": "1900-01-01"},
        {"planned_dt": "1970-01-01"},
    ])
    assert connection.execute("SELECT count(*) FROM clean_waiting WHERE planned_dt IS NULL").fetchone()[0] == 2
    preprocessing.create_analytical(connection, report)
    assert report["cleaning"]["waiting_exact_duplicates_removed"] == 0
    assert report["join"]["waiting_ambiguous_keys"] == 1
    assert report["join"]["unambiguous_matched_rows"] == 0
    assert report["join"]["analytical_rows"] == 1
    assert connection.execute("SELECT waiting_key_matched, region_origin_code FROM analytical").fetchone() == (False, None)
