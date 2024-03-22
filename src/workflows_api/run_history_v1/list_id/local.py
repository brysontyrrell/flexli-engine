from typing import Optional, Union

from pydantic import BaseModel, ConfigDict


class QueryStringParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    limit: Optional[int] = None


class RunHistoryV1Action(BaseModel):
    connector_type: Optional[
        str
    ] = None  # TODO: Temporary fix - see TODO in workflows_v1.create
    order: int
    type: str


class RunHistoryV1ListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nested_run_id: Optional[str] = None
    status: str
    reason: Optional[Union[str, dict]] = None
    time: str
    state: Optional[Union[dict, list]] = None
    action: Optional[RunHistoryV1Action] = None


class RunHistoryV1List(BaseModel):
    items: list[RunHistoryV1ListItem]
