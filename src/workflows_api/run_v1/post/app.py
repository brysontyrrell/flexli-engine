from datetime import datetime
import json
import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from ulid import ULID

from apis.middleware import api_middleware_v1
from apis.models import (
    ApiMiddlewareEvent,
    ApiResponse,
    BadRequest,
    CreatedResponse,
    DecimalEncoder,
)
from aws_utils import get_boto3_client, get_boto3_resource
from conditions import ConditionEvaluator
from database.workflows import read_workflow_version

logger = Logger()

TABLE_NAME = os.getenv("TABLE_NAME")
RUN_QUEUE_URL = os.getenv("RUN_QUEUE_URL")

dynamodb_table = get_boto3_resource("dynamodb").Table(TABLE_NAME)
sqs_client = get_boto3_client("sqs")


@api_middleware_v1(output_validator=CreatedResponse)
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    workflow_id = event.source_event.path_parameters["workflow_id"]
    workflow_version = int(event.source_event.path_parameters.get("version"))

    try:
        source_input = (
            event.source_event.json_body if event.source_event["body"] else {}
        )
    except json.JSONDecodeError:
        raise BadRequest(
            error_code="ValidationError",
            description="The request body must be valid JSON",
        )

    # TODO: This code is shared ith the Backend Runner and needs to be in a module

    workflow_data = read_workflow_version(
        dynamodb_table,
        tenant_id=event.tenant_id,
        workflow_id=workflow_id,
        workflow_version=workflow_version,
    )

    # Source-less workflows are allowed through the Run API
    if workflow_source := workflow_data.get("source"):
        if source_condition := workflow_source.get("condition"):
            if not ConditionEvaluator(source_condition).evaluate(source_input):
                raise BadRequest(
                    error_code="ConditionFailed",
                    description="The source condition failed.",
                )
        # TODO: Perform a transform is present

    new_run_id = str(ULID())

    sqs_client.send_message(
        QueueUrl=RUN_QUEUE_URL,
        MessageBody=json.dumps(
            {
                "tenant_id": event.tenant_id,
                "workflow_id": workflow_id,
                "workflow_version": workflow_data["version"],
                # "workflow_schema_version": workflow_data["schema_version"],
                "run_id": new_run_id,
                "source_input": source_input,
                "actions": workflow_data["actions"],
            },
            cls=DecimalEncoder,
        ),
    )

    timestamp = datetime.utcnow().isoformat()

    dynamodb_table.put_item(
        Item={
            "pk": f"T#{event.tenant_id}#WH#{workflow_id}",
            "sk": f"RH#{new_run_id}",
            "gsi1pk": f"T#{event.tenant_id}#WH",
            "gsi1sk": f"RH#{new_run_id}",
            "run_id": new_run_id,
            "workflow_id": workflow_id,
            "workflow_version": workflow_data["version"],
            "workflow_name": workflow_data["name"],
            "status": "queued",
            "start_time": timestamp,
        }
    )

    return ApiResponse(
        201,
        {"id": new_run_id, "href": f"/v1/run-history/{new_run_id}"},
    )
