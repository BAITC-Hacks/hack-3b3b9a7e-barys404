from pydantic import BaseModel, ConfigDict, Field, StrictBool


class AccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: StrictBool


class DeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login: str = Field(min_length=1, max_length=120)
