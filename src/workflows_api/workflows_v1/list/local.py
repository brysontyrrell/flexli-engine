from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from ulid import ULID


class QueryStringParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    releases_only: Optional[bool] = Field(default=None, alias="releases-only")

    @field_validator("id")
    def validate_id(cls, value):
        try:
            ULID.from_str(value)
        except:
            raise ValueError("Invalid resource ID")
        return value

    @field_validator("releases_only", mode="before")
    def bool_release(cls, value):
        return True if isinstance(value, str) else False


class WorkflowsListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: Optional[str] = None
    version: int
    is_release_version: bool
    schema_version: int


class WorkflowsList(BaseModel):
    items: list[WorkflowsListItem]
