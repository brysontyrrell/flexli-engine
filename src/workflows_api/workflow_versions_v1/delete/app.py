import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse
from database.workflows import delete_workflow_version

logger = Logger()

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = boto3.resource("dynamodb").Table(TABLE_NAME)


@api_middleware_v1
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    workflow_id = event.source_event.path_parameters["workflow_id"]
    workflow_version = event.source_event.path_parameters["version"]

    delete_workflow_version(
        dynamodb_table,
        tenant_id=event.tenant_id,
        workflow_id=workflow_id,
        workflow_version=workflow_version,
    )

    return ApiResponse(204)
