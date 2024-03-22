from typing import Optional

from pydantic import BaseModel, ConfigDict


class QueryStringParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    workflow: Optional[str] = None
    limit: Optional[int] = None


class RunV1ListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    run_id: str
    parent_run_id: Optional[str] = None
    workflow_id: str
    workflow_version: int
    workflow_name: str
    status: str
    start_time: str
    end_time: Optional[str] = None


class RunV1List(BaseModel):
    items: list[RunV1ListItem]
