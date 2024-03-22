import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
from pydantic import ValidationError, parse_obj_as

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse, BadRequest
from database.run_history import list_run_history

from local import QueryStringParams, RunV1List, RunV1ListItem

logger = Logger()

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = boto3.resource("dynamodb").Table(TABLE_NAME)

# TODO: Break out run history to its own table. DyDB stream processor to update LIST item.
# /v1/run-history  <- List of workflows executions and their latest status only


@api_middleware_v1(output_validator=RunV1List)
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)

    # TODO: Move to the middleware
    try:
        request_params = parse_obj_as(
            QueryStringParams,
            event.source_event.query_string_parameters or {},
        )
    except ValidationError as error:
        raise BadRequest(
            error_code="ValidationError",
            description="Invalid query string parameters",
            details=error,
        )

    response = list_run_history(
        dynamodb_table,
        tenant_id=event.tenant_id,
        workflow_id=request_params.workflow,
        limit=request_params.limit,
    )
    logger.debug(response)

    return ApiResponse(
        200,
        {
            "items": [
                parse_obj_as(RunV1ListItem, item).dict(exclude_none=True)
                for item in response
            ]
        },
    )
