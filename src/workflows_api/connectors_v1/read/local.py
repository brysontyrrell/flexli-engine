from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConnectorV1Read(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    type: str
    schema_version: int
    version: int
    # revision: int
    name: str
    description: Optional[str] = None
    config: dict
    events: Optional[list] = None
    actions: Optional[list] = None
