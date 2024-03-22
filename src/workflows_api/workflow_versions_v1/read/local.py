from decimal import Decimal
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, StrictBool

from conditions.models import Condition


class SourceRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    connector_id: Optional[str] = None  # TODO: Ensure ID is set for Flexli:CoreV1 items
    connector_type: str
    type: str
    condition: Optional[Condition] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class ActionRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    connector_id: Optional[str] = None  # TODO: Ensure ID is set for Flexli:CoreV1 items
    connector_type: str
    type: str
    order: int
    condition: Optional[Condition] = None
    parameters: dict
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class WorkflowsV1Read(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: Optional[str] = None
    version: int
    schema_version: int
    is_release_version: bool
    enabled: bool
    source: Optional[SourceRead] = None
    actions: list[ActionRead]
