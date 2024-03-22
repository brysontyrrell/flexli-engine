import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError, parse_obj_as

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse, BadRequest
from aws_utils import get_boto3_resource
from database.run_history import list_run_history_by_id

from local import QueryStringParams, RunHistoryV1List, RunHistoryV1ListItem

logger = Logger()

WORKFLOW_HISTORY_V1_TABLE_NAME = os.environ["WORKFLOW_HISTORY_V1_TABLE_NAME"]

workflow_history_v1_table = get_boto3_resource("dynamodb").Table(
    WORKFLOW_HISTORY_V1_TABLE_NAME
)


@api_middleware_v1(output_validator=RunHistoryV1List)
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)
    run_id = event.source_event.path_parameters["run_id"]

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

    response = list_run_history_by_id(
        workflow_history_v1_table,
        tenant_id=event.tenant_id,
        run_id=run_id,
        limit=request_params.limit,
    )
    logger.debug(response)

    return ApiResponse(
        200,
        {
            "items": [
                parse_obj_as(RunHistoryV1ListItem, item).dict(exclude_none=True)
                for item in response
            ]
        },
    )
