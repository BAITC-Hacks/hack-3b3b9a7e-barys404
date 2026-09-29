from backend.http import data
from backend.http.serialization import json_safe
from backend.modules.analytics import dashboard_data as db
from backend.modules.analytics.schemas import ReferralFilters
from backend.modules.auth.dependencies import resolve_hospital
from backend.modules.auth.store import Principal


def list_hospitals(
    query: ReferralFilters,
    search: str,
    limit: int,
    offset: int,
) -> dict:
    data.require_ready()
    filters = query.as_dict()
    table = db.hospital_directory(filters)
    if search:
        table = table.loc[
            table.organization_or_region.str.contains(
                search[:100], case=False, regex=False
            )
        ]
    return json_safe(
        {"total": len(table), "items": table.iloc[offset : offset + limit]}
    )


def get_hospital_overview(
    hospital_id: str,
    user: Principal,
    query: ReferralFilters,
) -> dict:
    hospital = resolve_hospital(user, hospital_id, required=True)
    data.require_ready()
    data.ensure_hospital_exists(hospital)
    filters = query.as_dict(hospital)
    comparison = db.hospital_directory(filters)
    row = comparison.iloc[0].to_dict() if not comparison.empty else None
    profiles = db.hospital_profiles(filters)
    return json_safe({"hospital": hospital, "stats": row, "profiles": profiles})
