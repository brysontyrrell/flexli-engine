from typing import Optional

from pydantic.v1 import BaseModel, Extra


class ConnectorV1Read(BaseModel):
    id: str
    type: str
    schema_version: int
    version: int
    # revision: int
    name: str
    description: Optional[str]
    config: dict
    events: Optional[list]
    actions: Optional[list]

    class Config:
        extra = Extra.ignore
