"""Exercise real HTTP dependencies and PostgreSQL isolation in a disposable schema."""
from functools import partial
import os
import time
import uuid

import pandas as pd
import psycopg
from psycopg import sql
import pytest
from fastapi.testclient import TestClient

from backend.auth import store
from backend.api import main as api
from backend.api.auth import SESSION_COOKIE
from backend.analytics import dashboard_data as db

PASSWORD = "test-only-strong-password"
BASE = "http://127.0.0.1:8000"


@pytest.fixture
def accounts(monkeypatch):
    if not os.environ.get("MEDFLOW_DATABASE_URL"):
        pytest.skip("Set MEDFLOW_DATABASE_URL to run PostgreSQL authorization tests")
    schema = "test_auth_" + uuid.uuid4().hex
    with psycopg.connect(store.database_url(), autocommit=True) as con:
        con.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    monkeypatch.setenv("MEDFLOW_AUTH_SCHEMA", schema)
    store.migrate()
    store.sync_organizations(["Hospital A", "Hospital B"])
    ids = {row["name"]: row["id"] for row in store.organizations()}
    for login, role, hid in [("a", "hospital_analyst", ids["Hospital A"]), ("b", "hospital_analyst", ids["Hospital B"]), ("gov", "government_analyst", None), ("admin", "platform_admin", None)]:
        store.create_user(login, login, PASSWORD, role, hid, must_change=False)
    try:
        yield ids
    finally:
        # Only a newly generated, test-owned schema is ever dropped.
        assert schema.startswith("test_auth_") and len(schema) == 42
        with psycopg.connect(store.database_url(), autocommit=True) as con:
            con.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def mutate(client, path, payload=None):
    csrf = client.get("/api/auth/csrf")
    assert csrf.status_code == 200
    return client.post(path, json=payload or {}, headers={"Origin": BASE, "X-CSRF-Token": csrf.json()["token"]})


def signed_in(login):
    client = TestClient(api.app, base_url=BASE)
    response = mutate(client, "/api/auth/login", {"login": login, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return client


@pytest.fixture
def analytical(monkeypatch, tmp_path):
    rows = []
    for hospital, region, profile, count in [("Hospital A", "01", "A-profile", 20), ("Hospital B", "02", "B-profile", 40)]:
        for i in range(count):
            rows.append({"hospital_mo": hospital, "region_origin_code": region, "bed_profile": profile,
                         "registration_dt": pd.Timestamp("2025-01-01") + pd.Timedelta(days=i % 28),
                         "outcome": "hospitalized", "target_eligible": True, "wait_days": 2.0})
    path = tmp_path / "analytical.parquet"
    pd.DataFrame(rows).to_parquet(path)
    monkeypatch.setattr(api, "ANALYTICAL_PATH", path)
    monkeypatch.setattr(api, "ready", lambda: {})
    for name in ("dimensions", "overview", "recent_activity", "hospital_directory", "hospital_profiles"):
        monkeypatch.setattr(db, name, partial(getattr(db, name), path=path))
    api.cached_dimensions.cache_clear()
    yield
    api.cached_dimensions.cache_clear()


def test_anonymous_cannot_read_any_business_route(accounts):
    with TestClient(api.app, base_url=BASE) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        for route in ["bootstrap", "overview", "hospitals", "compare", "models", "methodology", "hospital/overview?hospital_id=x", "hospital/forecast?hospital_id=x", "wait-options", "signals", "quality", "validation"]:
            result = client.get("/api/" + route)
            assert result.status_code == 401, (route, result.text)
            assert result.headers["cache-control"] == "no-store"
        assert mutate(client, "/api/predictions/wait", {}).status_code == 401
        assert mutate(client, "/api/briefings/preview", {}).status_code == 401
        assert mutate(client, "/api/briefings/pdf", {}).status_code == 401


def test_hospital_scope_applies_to_summary_filters_and_cached_dimensions(accounts, analytical):
    a = signed_in("a"); b = signed_in("b"); gov = signed_in("gov")
    for client, name, region, profile, expected in [(a, "Hospital A", "01", "A-profile", 20), (b, "Hospital B", "02", "B-profile", 40), (a, "Hospital A", "01", "A-profile", 20)]:
        boot = client.get("/api/bootstrap").json()
        assert boot["hospitals"] == [name]
        assert boot["regions"] == [region]
        assert boot["profiles"] == [profile]
        assert boot["hospital_ids"] == {name: accounts[name]}
        assert client.get("/api/overview").json()["stats"]["referrals"] == expected
    assert gov.get("/api/overview").json()["stats"]["referrals"] == 60
    assert len(gov.get("/api/bootstrap").json()["hospitals"]) == 2
    assert a.get("/api/overview?region=02").json()["stats"]["referrals"] == 0


def test_object_scope_checked_before_any_data_or_model_work(accounts, monkeypatch):
    def forbidden_work():
        pytest.fail("Analytical work ran before authorization")
    monkeypatch.setattr(api, "ready", forbidden_work)
    a = signed_in("a")
    for target in [accounts["Hospital B"], "unknown"]:
        for route in ["overview", "hospital/overview", "hospital/forecast", "wait-options", "signals", "quality"]:
            assert a.get(f"/api/{route}?hospital_id={target}").status_code == 404
        record = {"hospital_id": target, "icd10_ref_diag_code": "D", "bed_profile": "P", "territorial_type": "T", "referral_purpose": "R", "finance_source": "F", "registration_dt": "2025-03-20"}
        assert mutate(a, "/api/predictions/wait", record).status_code == 404
        payload = {'hospital_ids': [target], 'start': '2025-01-01', 'end': '2025-01-31'}
        assert mutate(a, '/api/briefings/preview', payload).status_code == 404
        assert mutate(a, '/api/briefings/pdf', {**payload, 'reviewed': True, 'review_token': '0' * 64}).status_code == 404
    for route in ["hospitals", "compare", "models"]:
        assert a.get("/api/" + route).status_code == 403
    admin = signed_in("admin")
    assert admin.get("/api/overview").status_code == 403
    for route in ['signals', 'quality', 'validation']:
        assert admin.get('/api/' + route).status_code == 403
    assert mutate(admin, '/api/briefings/preview', {}).status_code == 403
    assert mutate(admin, '/api/briefings/pdf', {}).status_code == 403


def test_new_monitoring_routes_keep_hospital_scope(accounts, analytical, monkeypatch):
    calls = []
    def feed(filters, *args, **kwargs):
        calls.append(filters)
        return {'items': [], 'total': 0}
    monkeypatch.setattr(api, 'signal_feed', feed)
    a = signed_in('a')
    assert a.get('/api/signals?start=2025-01-20&profile=A-profile').status_code == 200
    assert calls[-1]['hospital_mo'] == 'Hospital A'
    assert calls[-1]['bed_profile'] == 'A-profile'
    response = a.get('/api/quality').json()
    assert response['stats']['referrals'] == 20
    assert response['sources'] is None and response['preparation'] is None
    assert 'Hospital B' not in str(response)
    assert signed_in('gov').get('/api/quality').json()['stats']['referrals'] == 60


def test_temporal_groups_are_scoped_even_with_requested_foreign_dimension(accounts, monkeypatch):
    errors = {'mae': 2, 'baseline_mae': 4, 'rmse': 3}
    report = {'waiting': {'pooled': {**errors, 'observations': 999}, 'folds': [], 'minimum_group_size': 30,
                           'groups': {'hospital_mo': [dict(hospital_mo=name, observations=40, **errors) for name in ['Hospital A', 'Hospital B']],
                                      'region_origin_code': [{'region_origin_code': '02', 'observations': 999, **errors}]}},
              'forecast': {'pooled': errors, 'folds': [], 'by_horizon': []}, 'estimator_selection_overlap': True}
    monkeypatch.setattr(api, 'validation_status', lambda: {'available': True, 'report': report})
    a = signed_in('a')
    body = a.get('/api/validation?group=region_origin_code&search=Hospital%20B').json()
    assert body['groups']['dimension'] == 'hospital_mo'
    assert [row['name'] for row in body['groups']['items']] == ['Hospital A']
    assert body['waiting']['pooled']['mae'] == 2
    assert 'observations' not in body['waiting']['pooled']
    assert body['waiting_selection_overlap'] is True
    monkeypatch.setattr(api, 'validation_status', lambda: {'available': False, 'report': report})
    unavailable = a.get('/api/validation').json()
    assert unavailable['available'] is False and 'waiting' not in unavailable


def test_pdf_review_is_bound_to_server_data_filters_models_and_user(accounts, analytical, monkeypatch, tmp_path):
    from io import BytesIO
    from pypdf import PdfReader
    monkeypatch.setattr(db, 'compare_groups', partial(db.compare_groups, path=api.ANALYTICAL_PATH))
    evidence = {'status': {'available': True}, 'metrics': {'mae': 2.0, 'baseline_mae': 4.0, 'rmse': 3.0},
                'model_version': 'test-v1', 'test_period': {'start': '2025-01-01', 'end': '2025-01-31'}}
    monkeypatch.setattr(api, 'model_evidence', lambda *args: evidence.copy())
    a = signed_in('a')
    payload = {'hospital_ids': [accounts['Hospital A']], 'start': '2025-01-01', 'end': '2025-01-31', 'minimum': 10}
    preview = mutate(a, '/api/briefings/preview', payload)
    assert preview.status_code == 200, preview.text
    preview = preview.json()
    assert preview['snapshot']['aggregates'][0]['referrals'] == 20
    reviewed = {**payload, 'review_token': preview['review_token'], 'reviewed': True}
    assert mutate(a, '/api/briefings/pdf', {**reviewed, 'reviewed': False}).status_code == 422
    assert mutate(a, '/api/briefings/pdf', {**reviewed, 'reviewed': 'yes'}).status_code == 422
    assert mutate(a, '/api/briefings/pdf', {**reviewed, 'review_token': 'я' * 64}).status_code == 422
    assert mutate(a, '/api/briefings/pdf', {**reviewed, 'aggregates': []}).status_code == 422
    assert mutate(a, '/api/briefings/pdf', {**reviewed, 'end': '2025-01-30'}).status_code == 409
    assert mutate(a, '/api/briefings/pdf', {**reviewed, 'question': 'waiting'}).status_code == 409
    assert mutate(a, '/api/briefings/preview', {**payload, 'hospital_ids': payload['hospital_ids'] * 2}).status_code == 422
    assert mutate(signed_in('gov'), '/api/briefings/pdf', reviewed).status_code == 409
    pdf = mutate(a, '/api/briefings/pdf', reviewed)
    assert pdf.status_code == 200, pdf.text[:100]
    assert pdf.headers['content-type'] == 'application/pdf'
    assert pdf.headers['cache-control'] == 'no-store'
    reader = PdfReader(BytesIO(pdf.content))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert 'Hospital A' in text and 'Hospital B' not in text
    assert 'test-v1' in text and 'Проверка человеком' in text
    evidence['model_version'] = 'test-v2'
    assert mutate(a, '/api/briefings/pdf', reviewed).status_code == 409
    evidence['model_version'] = 'test-v1'
    frame = pd.read_parquet(api.ANALYTICAL_PATH)
    frame.loc[frame.hospital_mo.eq('Hospital A'), 'wait_days'] = 9
    frame.to_parquet(api.ANALYTICAL_PATH)
    assert mutate(a, '/api/briefings/pdf', reviewed).status_code == 409


def test_csrf_rotation_logout_and_cookie_flags(accounts):
    client = TestClient(api.app, base_url=BASE)
    assert client.post("/api/auth/login", json={"login": "a", "password": PASSWORD}).status_code == 403
    token = client.get("/api/auth/csrf").json()["token"]
    assert client.post("/api/auth/login", json={"login": "a", "password": PASSWORD}, headers={"Origin": "https://evil.example", "X-CSRF-Token": token}).status_code == 403
    response = mutate(client, "/api/auth/login", {"login": "a", "password": PASSWORD})
    assert "HttpOnly" in response.headers["set-cookie"] and "SameSite=lax" in response.headers["set-cookie"]
    cookie = client.cookies.get(SESSION_COOKIE)
    assert client.post("/api/auth/logout", json={}, headers={"Origin": BASE, "X-CSRF-Token": token}).status_code == 403
    assert mutate(client, "/api/auth/logout").status_code == 200
    client.cookies.set(SESSION_COOKIE, cookie)
    assert client.get("/api/auth/me").status_code == 401


def test_role_or_password_change_and_disable_revoke_sessions(accounts):
    a = signed_in("a")
    store.update_user("a", hospital_id=accounts["Hospital B"])
    assert a.get("/api/auth/me").status_code == 401
    a = signed_in("a")
    assert a.get("/api/auth/me").json()["hospital_id"] == accounts["Hospital B"]
    store.update_user("a", active=False)
    assert a.get("/api/auth/me").status_code == 401
    assert mutate(a, "/api/auth/login", {"login": "a", "password": PASSWORD}).status_code == 401
    b = signed_in("b")
    assert mutate(b, "/api/auth/change-password", {"current_password": PASSWORD, "new_password": "a-new-strong-password"}).status_code == 200
    assert b.get("/api/auth/me").status_code == 401
    with pytest.raises(ValueError, match="последнего"):
        store.update_user("admin", active=False)


def test_expiry_and_missing_organization_fail_closed(accounts, analytical):
    a = signed_in("a")
    with store.connection() as con:
        con.execute("UPDATE sessions SET last_active=%s", (time.time() - 1801,))
    assert a.get("/api/auth/me").status_code == 401
    a = signed_in("a")
    with store.connection() as con:
        con.execute("UPDATE organizations SET active=0 WHERE id=%s", (accounts["Hospital A"],))
    assert a.get("/api/bootstrap").status_code == 403
    assert a.get("/api/overview").status_code == 403


def test_login_rate_limit_and_cannot_choose_role(accounts):
    client = TestClient(api.app, base_url=BASE)
    assert mutate(client, "/api/auth/login", {"login": "a", "password": PASSWORD, "role": "government_analyst"}).status_code == 422
    for _ in range(10):
        assert mutate(client, "/api/auth/login", {"login": "a", "password": "wrong"}).status_code == 401
    assert mutate(client, "/api/auth/login", {"login": "a", "password": PASSWORD}).status_code == 429


def test_temporary_password_blocks_analytics_and_login_does_not_need_data(accounts, monkeypatch):
    monkeypatch.setattr(api, "ready", lambda: pytest.fail("Login must not require analytical data"))
    store.update_user("a", password=PASSWORD)
    a = signed_in("a")
    assert a.get("/api/auth/me").json()["must_change_password"] is True
    assert a.get("/api/overview").status_code == 403
    assert mutate(a, "/api/auth/change-password", {"current_password": PASSWORD, "new_password": "another-test-password"}).status_code == 200
