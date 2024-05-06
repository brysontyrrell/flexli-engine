import json
import os
from typing import Any, Callable, Dict, Optional, Type

from aws_lambda_powertools import Logger
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel, ValidationError, parse_obj_as

from apis.models import (
    ApiMiddlewareEvent,
    ApiError,
    APIGatewayProxyEvent,
    ApiResponse,
    BadRequest,
    PathParams,
    UnsupportedMediaType,
)
from aws_utils import get_boto3_resource
from database.tenants import get_user_context

TABLE_NAME = os.getenv("TABLE_NAME")

__all__ = ["api_middleware_v1"]

logger = Logger(child=True)
dynamodb_table = get_boto3_resource("dynamodb").Table(TABLE_NAME)


@lambda_handler_decorator
def api_middleware_v1(
    handler: Callable[[ApiMiddlewareEvent, LambdaContext], ApiResponse],
    event: Dict[str, Any],
    context: LambdaContext,
    input_validator: Type[BaseModel] = None,
    input_options: Optional[Dict[str, Any]] = None,
    output_validator: Type[BaseModel] = None,
):
    event_data = APIGatewayProxyEvent(event)

    try:
        handler_event = ApiMiddlewareEvent(source_event=event_data)

        # Validate JSON body
        if input_validator:
            logger.debug("Triggered input validation")

            if event_data.get_header_value("Content-Type") != "application/json":
                raise UnsupportedMediaType(
                    description="The request body must be of type application/json"
                )

            # Default options for dictionary output from the input model.
            if not input_options:
                # input_options = {"exclude_unset": True}
                input_options = {}

            try:
                # validated_input = input_validator(**event_data.json_body)
                handler_event.model = parse_obj_as(
                    input_validator, event_data.json_body
                )
            except (TypeError, json.JSONDecodeError):  # json_body is not a dictionary
                raise BadRequest(
                    description="The request must include a valid JSON body",
                )
            except ValidationError as error:
                raise BadRequest(
                    error_code="ValidationError",
                    description="The request body failed validation",
                    details=error,
                )
            else:
                handler_event.model_data = handler_event.model.dict(**input_options)

        # Validate path parameters
        if event_data.path_parameters:
            try:
                PathParams.model_validate(event_data.path_parameters)
            except ValueError:
                raise BadRequest(description="Invalid resource ID")

        # Obtain user context after validations pass
        user_context = get_user_context(
            table_resource=dynamodb_table,
            sub=event_data.request_context.authorizer.claims["sub"],
        )

        handler_event.tenant_id = user_context.tenant_id

        api_response = handler(handler_event, context)

        if output_validator:
            logger.debug("Triggered output validation")
            try:
                parse_obj_as(output_validator, api_response.body)
            except (TypeError, ApiError) as error:
                logger.exception("Output validation failed")
                logger.debug(
                    error.response() if isinstance(error, ApiError) else str(error)
                )
                raise ApiError(
                    error_code="InternalServerError",
                    description="The server provided an invalid response.",
                )

    except ApiError as error:
        # TODO: Request ID must propagate across logging/downstream
        api_response = error.response(request_id=event_data.request_context.request_id)
        logger.debug(api_response)
    except Exception:
        raise

    return api_response.api_proxy_response()
