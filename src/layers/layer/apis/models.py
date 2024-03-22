from dataclasses import dataclass
import decimal
import json
from typing import Any, ClassVar, Dict, Optional, Union

import jmespath
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from ulid import ULID


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        else:
            return json.JSONEncoder.default(self, obj)


@dataclass
class ApiMiddlewareEvent:
    source_event: APIGatewayProxyEvent
    tenant_id: Optional[str] = None
    model: Optional[Any] = None
    model_data: Optional[dict] = None


class PathParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validates_path_ids(cls, values):
        for k, v in values.items():
            if k.endswith("_id"):
                ULID.from_str(v)
        return values


@dataclass
class ApiResponse:
    status_code: int
    body: Optional[dict] = ""
    headers: Optional[dict] = None

    def __post_init__(self):
        if self.body and not self.headers:
            self.headers = {"Content-Type": "application/json"}

    def api_proxy_response(self):
        return {
            "statusCode": self.status_code,
            "body": json.dumps(self.body, cls=DecimalEncoder),
            "headers": self.headers,
        }


class CreatedResponse(BaseModel):
    id: str = Field(title="Resource ID", description="The resource identifier.")
    href: str = Field(
        title="Resource Location", description="The URI to the created resource."
    )


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(
        description="A request identifier used for troubleshooting",
        examples=["20554228-97b1-46ce-9236-a70dc58f8b6e"],
        title="Request ID",
    )
    error_code: str = Field(
        description="The error code",
        examples=["ValidationError"],
        title="Error code",
    )
    description: str = Field(
        description="A description of the error",
        examples=["The request body failed validation."],
        title="Description",
    )
    details: Optional[Dict[str, Any]] = Field(
        description="Optional error specific properties",
        examples=[
            {
                "validation_errors": [
                    {"path": "$", "description": "'id' is a required property"}
                ]
            }
        ],
        title="Details",
    )


def json_schema_validation_error_path(error: Any) -> str:
    path = ""

    for i in error.path:
        if isinstance(i, int):
            path += f"[{i}]"
        else:
            path += f".{i}"

    # Property name is not in the 'path' if the validator is 'required'
    if error.validator == "required":
        if len(path) > 0 and path[-1] != "]":
            path += "."
        path += error.message.split("'")[1]

    return path.lstrip(".")


def json_schema_validation(
    data: dict, validator: Draft202012Validator
) -> Union[dict, None]:
    """TODO: Should this be raising an exception with the error details?"""
    validation_errors = []
    for error in validator.iter_errors(data):
        error_path = json_schema_validation_error_path(error)
        # If the error was caused by a string that started with an expression token skip
        if isinstance(
            error_value := jmespath.search(error_path, data=data), str
        ) and error_value.startswith("::"):
            print(f"Skipping error: {error.message}")
            continue
        validation_errors.append(
            {
                "path": error_path,
                "description": str(error.message),
            }
        )
    if validation_errors:
        return {"validation_errors": validation_errors}
    else:
        return None


def model_validation_error_path(location: tuple, model_name: str) -> str:
    path = ""
    for i in location:
        if i in ("__root__", model_name):
            continue
        elif isinstance(i, int):
            path += f"[{i}]"
        else:
            path += f".{i}"
    return path.lstrip(".")


def model_validation_error_details(error: ValidationError) -> dict:
    validation_errors = []

    try:
        # In Annotated models the evaluated model is nested in a
        # `ValidationError` within the `args` of the root error.
        model_name = error.args[0][0].exc.model.__name__
    except AttributeError:
        model_name = error.model.__name__

    print(model_name)

    for e in error.errors():
        validation_errors.append(
            {
                "path": model_validation_error_path(
                    location=e["loc"], model_name=model_name
                ),
                "description": e["msg"],
            }
        )

    return {"validation_errors": validation_errors}


@dataclass
class ApiError(Exception):
    """Base API Exception"""

    status_code: ClassVar[int] = 500
    default_description: ClassVar[str] = "Internal Server Error"
    error_code: Optional[str] = None
    description: Optional[str] = None
    details: Optional[Union[dict, ValidationError]] = None

    def response(self, request_id: Optional[str] = None):
        body = {
            "id": request_id,
            "error_code": self.error_code,
            "description": self.description or self.default_description,
        }

        if self.details:
            body["details"] = (
                self.details
                if isinstance(self.details, dict)
                else model_validation_error_details(self.details)
            )

        return ApiResponse(self.status_code, body)


class BadRequest(ApiError):
    """400 Bad Request"""

    status_code = 400
    default_description = "Bad Request"


class Forbidden(ApiError):
    """403 Forbidden"""

    status_code = 403
    default_description = "Forbidden"


class NotFound(ApiError):
    """404 Not Found"""

    status_code = 404
    default_description = "Not Found"


class RequestTimeout(ApiError):
    """408 Request Timeout"""

    status_code = 408
    default_description = "Request Timeout"


class Conflict(ApiError):
    """408 Request Timeout"""

    status_code = 409
    default_description = "Conflict"


class UnsupportedMediaType(ApiError):
    """415 Unsupported Media Type"""

    status_code = 415
    default_description = "Unsupported Media Type"
