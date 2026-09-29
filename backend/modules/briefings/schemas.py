from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BriefingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hospital_ids: list[str] = Field(min_length=1, max_length=3)
    start: date
    end: date
    region: str | None = Field(default=None, max_length=300)
    profile: str | None = Field(default=None, max_length=300)
    minimum: int = Field(default=30, ge=10, le=1000)
    question: Literal["waiting", "flow", "refusals"] = "flow"


class ReviewedBriefingRequest(BriefingRequest):
    reviewed: bool = Field(strict=True)
    review_token: str = Field(pattern=r"^[0-9a-f]{64}$")
