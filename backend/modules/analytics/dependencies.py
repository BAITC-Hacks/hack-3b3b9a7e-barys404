from datetime import date

from backend.modules.analytics.schemas import ReferralFilters


def referral_filters(
    start: date | None = None,
    end: date | None = None,
    region: str | None = None,
    profile: str | None = None,
) -> ReferralFilters:
    return ReferralFilters(start, end, region, profile)
