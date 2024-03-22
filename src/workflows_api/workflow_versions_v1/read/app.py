import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import parse_obj_as

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse
from aws_utils import get_boto3_resource
from database.workflows import read_workflow_version

from local import WorkflowsV1Read

logger = Logger()

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = get_boto3_resource("dynamodb").Table(TABLE_NAME)


@api_middleware_v1
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    workflow_id = event.source_event.path_parameters["workflow_id"]
    workflow_version = event.source_event.path_parameters["version"]

    response = read_workflow_version(
        dynamodb_table,
        tenant_id=event.tenant_id,
        workflow_id=workflow_id,
        workflow_version=workflow_version,
    )

    return ApiResponse(
        200, parse_obj_as(WorkflowsV1Read, response).dict(exclude_none=True)
    )
