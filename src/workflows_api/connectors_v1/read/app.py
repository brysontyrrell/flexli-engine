import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
from pydantic import parse_obj_as

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse
from database.connectors import read_connector

from local import ConnectorV1Read

logger = Logger()

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = boto3.resource("dynamodb").Table(TABLE_NAME)


@api_middleware_v1(output_validator=ConnectorV1Read)
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    connector_id = event.source_event.path_parameters["connector_id"]
    response = read_connector(
        dynamodb_table, tenant_id=event.tenant_id, connector_id=connector_id
    )
    return ApiResponse(200, parse_obj_as(ConnectorV1Read, response).dict())
