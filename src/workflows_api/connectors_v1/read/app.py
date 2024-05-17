from aws_lambda_powertools import Logger

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse
from database.connectors import read_connector

from local import ConnectorV1Read

logger = Logger()


@api_middleware_v1(output_validator=ConnectorV1Read)
def lambda_handler(event: ApiMiddlewareEvent, context) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)

    connector_id = event.source_event.path_parameters["connector_id"]
    response = read_connector(tenant_id=event.tenant_id, connector_id=connector_id)
    return ApiResponse(200, ConnectorV1Read.model_validate(response).model_dump())
