from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class EncryptedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    CiphertextBlob: bytes
    KeyId: str


class OAuth2ClientCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["OAuth2Client"]
    client_id: str
    client_secret: str
    token_url: str
    basic_auth: bool


class BearerTokenCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["BearerToken"]
    bearer_token: str


class ApiKeyCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["ApiKey"]
    api_key: str
    api_key_header: str
    # TODO: Support query string parameter


class AwsSigV4Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["AwsSigV4"]
    access_key_id: str
    secret_access_key: str


class EventConfigTypes(str, Enum):
    basic_auth = "BasicAuth"
    api_key = "ApiKey"
    hmac_sha256 = "HmacSha256"


class EventsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: EventConfigTypes
    content_type: Literal["application/json"]
    event_type_keypath: str


class HttpMethods(str, Enum):
    post = "post"
    get = "get"
    put = "put"
    patch = "patch"
    delete = "delete"
    head = "head"
    options = "options"


class ConnectorV1Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: Optional[str] = None
    description: Optional[str] = None
    method: HttpMethods
    path: str
    headers: Optional[dict[str, str]] = None
    query: Optional[dict[str, str]] = None
    body: Optional[Union[str, dict]] = None
    parameters: Optional[dict] = None


class ConnectorV1Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    description: str
    schema_: dict = Field(..., alias="schema")


class ConnectorV1Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str  # TODO: regex needed
    base_path: Optional[str] = None
    default_headers: Optional[dict[str, str]] = None
    credentials: Optional[
        Annotated[
            Union[OAuth2ClientCredentials, BearerTokenCredentials, ApiKeyCredentials],
            Field(discriminator="type"),
        ]
    ] = None
    events: Optional[EventsConfig] = None


class ConnectorV1Create(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    description: str
    schema_version: Literal[1]
    config: ConnectorV1Config
    events: Optional[list[ConnectorV1Event]] = Field(default_factory=list)
    actions: list[ConnectorV1Action] = Field(default_factory=list)


# TODO: Action and Event Types MUST be unique!
