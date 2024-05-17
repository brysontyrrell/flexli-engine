from aws_lambda_powertools import Logger

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse, BadRequest
from database.workflows import delete_workflow_version

logger = Logger()


@api_middleware_v1
def lambda_handler(event: ApiMiddlewareEvent, context) -> ApiResponse:
    logger.append_keys(tenant_id=event.tenant_id)

    workflow_id = event.source_event.path_parameters["workflow_id"]
    # TODO: Move path validation to API middleware
    try:
        workflow_version = int(event.source_event.path_parameters["version"])
    except (TypeError, ValueError):
        raise BadRequest(
            error_code="ValidationError", description="Invalid version value"
        )

    delete_workflow_version(
        tenant_id=event.tenant_id,
        workflow_id=workflow_id,
        workflow_version=workflow_version,
    )

    return ApiResponse(204)
