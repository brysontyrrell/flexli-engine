import os

from aws_lambda_powertools import Logger

from apis.middleware import api_middleware_v1
from apis.models import ApiMiddlewareEvent, ApiResponse, CreatedResponse
from aws_utils import get_boto3_client
from database.connectors import create_connector

from local import ConnectorV1Create, EncryptedItem

logger = Logger()

DEFAULT_KEY_ID = os.getenv("DEFAULT_KEY_ID")

kms_client = get_boto3_client("kms")


@api_middleware_v1(input_validator=ConnectorV1Create, output_validator=CreatedResponse)
def lambda_handler(event: ApiMiddlewareEvent, context) -> ApiResponse:
    if (
        hasattr(event.model.config, "credentials")
        and event.model.config.credentials is not None
    ):
        encrypted_credentials = kms_client.encrypt(
            KeyId=DEFAULT_KEY_ID,
            Plaintext=event.model.config.credentials.json(),
        )

        del event.model_data["config"]["credentials"]
        event.model_data["credentials"] = EncryptedItem(**encrypted_credentials).dict()

    new_connector_id = create_connector(
        tenant_id=event.tenant_id,
        data=event.model_data,
    )

    return ApiResponse(
        201, {"id": new_connector_id, "href": f"/v1/connectors/{new_connector_id}"}
    )
