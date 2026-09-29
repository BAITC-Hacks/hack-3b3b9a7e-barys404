from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class WaitingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hospital_id: str = Field(min_length=1, max_length=80)
    icd10_ref_diag_code: str = Field(min_length=1)
    bed_profile: str = Field(min_length=1)
    territorial_type: str = Field(min_length=1)
    referral_purpose: str = Field(min_length=1)
    finance_source: str = Field(min_length=1)
    registration_dt: date
