from aws_lambda_powertools import Logger

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse
from database.connectors import delete_connector

logger = Logger()


@api_middleware_v1
def lambda_handler(event: ApiMiddlewareEvent, context) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)

    connector_id = event.source_event.path_parameters["connector_id"]
    delete_connector(tenant_id=event.tenant_id, connector_id=connector_id)
    return ApiResponse(204)
