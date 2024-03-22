from typing import Optional

from pydantic.v1 import BaseModel, Extra, root_validator


# from local import ConnectorsV1ListItem; from pydantic import parse_obj_as
# parse_obj_as(ConnectorsV1ListItem, {"id": "abc123", "type": "JumpCloud", "schema_version": 1, "name": "JumpCloud", "version": 1, "context": {"actions": ["ListDeviceGroupsForDevice"]}})
class ConnectorsV1ListItem(BaseModel):
    id: str
    type: str
    schema_version: int
    version: int
    # revision: int
    name: str
    description: Optional[str]
    events: list[str]
    actions: list[str]

    @root_validator(pre=True)
    def events_and_actions(cls, values: dict) -> dict:
        """The context object is merged into the top-level keys if present."""
        if "context" in values:
            values["events"] = values["context"].get("events", [])
            values["actions"] = values["context"].get("actions", [])
        return values

    class Config:
        extra = Extra.ignore


class ConnectorsV1List(BaseModel):
    items: list[ConnectorsV1ListItem]
