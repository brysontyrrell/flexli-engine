from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic.v1 import BaseModel, Extra, Field


class EncryptedItem(BaseModel):
    CiphertextBlob: bytes
    KeyId: str

    class Config:
        extra = Extra.ignore


class OAuth2ClientCredentials(BaseModel, extra=Extra.forbid):
    type: Literal["OAuth2Client"]
    client_id: str
    client_secret: str
    token_url: str
    basic_auth: bool


class BearerTokenCredentials(BaseModel, extra=Extra.forbid):
    type: Literal["BearerToken"]
    bearer_token: str


class ApiKeyCredentials(BaseModel, extra=Extra.forbid):
    type: Literal["ApiKey"]
    api_key: str
    api_key_header: str
    # TODO: Support query string parameter


class AwsSigV4Credentials(BaseModel, extra=Extra.forbid):
    type: Literal["AwsSigV4"]
    access_key_id: Optional[str]
    secret_access_key: Optional[str]
    # role_arn: Optional[str]


class HttpMethods(str, Enum):
    post = "post"
    get = "get"
    put = "put"
    patch = "patch"
    delete = "delete"
    head = "head"
    options = "options"


class ConnectorV1Action(BaseModel):
    type: str
    name: Optional[str]
    description: Optional[str]
    method: HttpMethods
    path: str
    headers: Optional[dict[str, str]]
    query: Optional[dict[str, str]]
    body: Optional[Union[str, dict]]
    parameters: Optional[dict]

    class Config:
        extra = Extra.forbid


class ConnectorV1Event(BaseModel):
    type: str
    name: str
    description: str
    schema_: dict = Field(..., alias="schema")

    class Config:
        extra = Extra.forbid


class ConnectorV1Config(BaseModel):
    host: str  # TODO: regex needed
    base_path: Optional[str]
    credentials: Optional[
        Annotated[
            Union[OAuth2ClientCredentials, BearerTokenCredentials, ApiKeyCredentials],
            Field(discriminator="type"),
        ]
    ]
    default_headers: Optional[dict[str, str]]

    class Config:
        extra = Extra.forbid


class ConnectorV1Create(BaseModel):
    type: str
    name: str
    description: str
    schema_version: Literal[1]
    config: ConnectorV1Config
    events: Optional[list[ConnectorV1Event]] = Field(default_factory=list)
    actions: list[ConnectorV1Action] = Field(default_factory=list)

    class Config:
        extra = Extra.forbid


# TODO: Action and Event Types MUST be unique!
