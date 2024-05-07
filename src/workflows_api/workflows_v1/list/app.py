import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
from pydantic import ValidationError

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse, BadRequest
from database.workflows import list_workflows

from local import QueryStringParams, WorkflowsList

logger = Logger()

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = boto3.resource("dynamodb").Table(TABLE_NAME)


@api_middleware_v1(output_validator=WorkflowsList)
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)

    try:
        request_params = QueryStringParams.model_validate(
            event.source_event.query_string_parameters or {},
        )
    except ValidationError as error:
        raise BadRequest(
            error_code="ValidationError",
            description="Invalid query string parameters",
            details=error,
        )

    response = list_workflows(
        dynamodb_table,
        tenant_id=event.tenant_id,
        workflow_id=request_params.id,
        releases_only=request_params.releases_only,
    )

    return ApiResponse(
        200,
        WorkflowsList.model_validate(
            {"items": [item for item in response]}
        ).model_dump(),
    )
