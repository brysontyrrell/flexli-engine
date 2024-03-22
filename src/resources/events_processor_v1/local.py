import copy
from datetime import datetime
import json

from pydantic import BaseModel, ConfigDict, model_validator


class Event(BaseModel):
    type: str
    source: str
    id: str
    tenant_id: str
    connector_id: str
    connector_type: str
    event_type: str
    time: datetime
    data: dict

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    def attr_conversion(cls, values):
        split_type = values["type"].rpartition(":")
        values["connector_type"] = split_type[0]
        values["event_type"] = split_type[-1]

        values["tenant_id"] = copy.copy(values["tenantid"])
        values["connector_id"] = copy.copy(values["connectorid"])

        if isinstance(values["data"], str):
            values["data"] = json.loads(values["data"])
        return values


class EventToSend(BaseModel):
    workflow: dict
    event: Event
