from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator


class ConnectorsV1ListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    type: str
    schema_version: int
    version: int
    # revision: int
    name: str
    description: Optional[str]
    events: list[str]
    actions: list[str]

    @model_validator(mode="before")
    def events_and_actions(cls, values: dict) -> dict:
        """The context object is merged into the top-level keys if present."""
        if "context" in values:
            values["events"] = values["context"].get("events", [])
            values["actions"] = values["context"].get("actions", [])
        return values


class ConnectorsV1List(BaseModel):
    items: list[ConnectorsV1ListItem]
