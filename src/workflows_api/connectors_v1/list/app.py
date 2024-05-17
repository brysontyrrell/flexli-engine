from aws_lambda_powertools import Logger

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse
from database.connectors import list_connectors

from local import ConnectorsV1List

logger = Logger()


@api_middleware_v1(output_validator=ConnectorsV1List)
def lambda_handler(event: ApiMiddlewareEvent, context) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)

    response = list_connectors(tenant_id=event.tenant_id)
    return ApiResponse(
        200,
        ConnectorsV1List.model_validate(
            {"items": [item for item in response]}
        ).model_dump(),
    )
