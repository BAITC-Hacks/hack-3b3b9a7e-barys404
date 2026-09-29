from functools import lru_cache

import pandas as pd

from backend.http import data
from backend.http.serialization import json_safe
from backend.modules.analytics import dashboard_data as db
from backend.modules.analytics import repository
from backend.modules.analytics.schemas import ComparisonGroup, ReferralFilters
from backend.modules.auth import store
from backend.modules.auth.dependencies import resolve_hospital
from backend.modules.auth.scope import DataScope
from backend.modules.auth.store import Principal


@lru_cache(maxsize=4)
def cached_dimensions(version: tuple[int, int], hospital: str | None = None) -> dict:
    return db.dimensions(filters=DataScope(hospital).apply({}))


def get_bootstrap(user: Principal) -> dict:
    hospital = resolve_hospital(user, None)

    data.require_ready()
    if hospital:
        data.ensure_hospital_exists(hospital)

    dimensions = cached_dimensions(db.file_version(data.ANALYTICAL_PATH), hospital)
    hospital_ids = _get_hospital_catalog(user, dimensions)

    return json_safe(
        {
            "period": {
                "start": str(dimensions["dates"]["first"])[:10],
                "end": str(dimensions["dates"]["last"])[:10],
            },
            "regions": dimensions["region_origin_code"],
            "profiles": [
                value for value in dimensions["bed_profile"] if value != "__MISSING__"
            ],
            "hospitals": list(hospital_ids),
            "hospital_ids": hospital_ids,
            "featured_hospital": hospital or next(iter(hospital_ids), ""),
        }
    )


def _get_hospital_catalog(user: Principal, dimensions: dict) -> dict[str, str]:
    hospital_id = user.hospital_id if user.role == "hospital_analyst" else None
    catalog = store.organizations(hospital_id)
    return {
        row["name"]: row["id"]
        for row in catalog
        if row["name"] in dimensions["hospital_mo"]
    }


def get_overview(
    query: ReferralFilters,
    user: Principal,
    hospital_id: str | None = None,
) -> dict:
    hospital = resolve_hospital(user, hospital_id)

    data.require_ready()
    filters = DataScope(hospital).apply(query.as_dict())

    stats = db.overview(filters)
    trend = repository.referral_trend(filters, data.ANALYTICAL_PATH)
    period, changes = db.recent_activity(filters)
    attention = _select_attention(changes, hospital)

    return json_safe(
        {
            "stats": stats,
            "trend": trend,
            "attention_period": period,
            "attention": attention,
        }
    )


def _select_attention(changes: pd.DataFrame, hospital: str | None) -> pd.DataFrame:
    if hospital and not changes.empty:
        changes = changes.loc[changes.hospital.eq(hospital)]
    if changes.empty:
        return changes

    enough_observations = (changes.previous >= 10) & (changes.current >= 10)
    growing = changes.change_pct > 0
    return (
        changes.loc[enough_observations & growing]
        .sort_values("change_pct", ascending=False)
        .head(4)
    )


def compare_hospitals(
    query: ReferralFilters,
    group: ComparisonGroup,
    minimum: int,
    selected: str,
    search: str,
) -> dict:
    data.require_ready()
    filters = query.as_dict()

    table = db.compare_groups(filters, group_by=group, minimum=minimum)
    names = [name for name in selected.split("|") if name][:3]
    table = _filter_comparison(table, search, names)
    table = _prioritize_selected(table, names)

    return json_safe({"items": table.head(50), "total": len(table)})


def _filter_comparison(
    table: pd.DataFrame, search: str, names: list[str]
) -> pd.DataFrame:
    if not search:
        return table

    matches = table.organization_or_region.str.contains(
        search[:100], case=False, regex=False
    )
    return table.loc[matches | table.organization_or_region.isin(names)]


def _prioritize_selected(table: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    if not names:
        return table

    selected = table.organization_or_region.isin(names)
    return pd.concat([table.loc[selected], table.loc[~selected]], ignore_index=True)
