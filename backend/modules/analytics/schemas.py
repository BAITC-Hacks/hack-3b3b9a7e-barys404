from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from fastapi import HTTPException

ComparisonGroup = Literal["hospital_mo", "region_origin_code"]


@dataclass(frozen=True)
class ReferralFilters:
    start: date | None = None
    end: date | None = None
    region: str | None = None
    profile: str | None = None

    def as_dict(self, hospital: str | None = None) -> dict[str, Any]:
        if self.start and self.end and self.start > self.end:
            raise HTTPException(422, "Начало периода должно быть раньше конца.")
        filters = {
            "start": self.start,
            "end": self.end,
            "region_origin_code": self.region,
            "bed_profile": self.profile,
            "hospital_mo": hospital,
        }
        return {key: value for key, value in filters.items() if value is not None}
