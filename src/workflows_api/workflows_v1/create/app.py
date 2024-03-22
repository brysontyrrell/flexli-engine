import os
from functools import lru_cache
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from jsonschema import Draft202012Validator, FormatChecker

from apis.middleware import api_middleware_v1
from apis.models import (
    ApiMiddlewareEvent,
    ApiResponse,
    CreatedResponse,
    BadRequest,
    json_schema_validation,
)
from aws_utils import get_boto3_resource
from database.connectors import list_connectors, read_connector
from database.workflows import create_workflow

from local import WorkflowsV1Create


logger = Logger()
tracer = Tracer()

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = get_boto3_resource("dynamodb").Table(TABLE_NAME)


@lru_cache
def cached_read_connector(table_resource, tenant_id: str, connector_id: str) -> dict:
    return read_connector(
        table_resource=dynamodb_table,
        tenant_id=tenant_id,
        connector_id=connector_id,
    )


def find_connector_by_id(
    tenant_id: str, connector_id: str, connectors_list: list[dict]
) -> dict[str, Any]:
    """Return a connector object in a list of connectors using the provided ID.
    Reference ``ConnectorsListItem`` for object attributes.
    """
    if next(
        (i for i in connectors_list if i["id"] == connector_id),
        None,
    ):
        return cached_read_connector(
            table_resource=dynamodb_table,
            tenant_id=tenant_id,
            connector_id=connector_id,
        )
    else:
        raise BadRequest(
            error_code="InvalidConnectorId",
            description="An invalid connector was provided",
            details={"id": connector_id},
        )


def find_item_by_key(items: list[dict], key: str, value: str) -> dict:
    for i in items:
        if i.get(key) == value:
            return i


@api_middleware_v1(input_validator=WorkflowsV1Create, output_validator=CreatedResponse)
def lambda_handler(event: ApiMiddlewareEvent, context: LambdaContext) -> ApiResponse:
    tenant_id = event.tenant_id
    workflow_data = event.model_data

    # Get the list of all current connectors
    # The 'type' is included in this return.
    current_tenant_connectors = list_connectors(dynamodb_table, tenant_id)
    logger.debug(current_tenant_connectors or "No connectors found for this tenant")

    """List response items:
    {
        'id': 'abc123',
        'type': 'ConnectorType',
        'schema_version': 1,
        'name': 'Connector Name',
        'version': 1,
        'context': {
            'events': ['EventType'],
            'actions': ['ActionType']
        }
    }
    """

    # This function relied on having a built-in mapping of allowed events/models in code.
    # The connector list should include arrays of the events and actions.

    # The events and actions can be embedded here.
    # List endpoints will merge context keys back into the main object.

    # The workflow must be traversed to collect all connector IDs and event/action types.
    # All connectors will then be read in a batch get items call to collect (cache responses).
    # Schema validation can then be performed.

    # TODO: This code must be namespace aware

    # 'source' is not an array (only one source per workflow in v1)
    if workflow_source := workflow_data.get("source"):
        if workflow_source["type"].startswith("Flexli:CoreV1:"):
            # Pydantic model currently validates
            # TODO: Replace Pydantic models in input validation with an embedded JSON schema
            # The embedded JSON schema will be able to leverage the processing below

            # TODO: Convert to using `{ConId}:{ConType}:{ActType}` for action types
            workflow_source["connector_id"] = "Flexli:CoreV1"

            if workflow_source["type"] == "Flexli:CoreV1:CustomEvent":
                # Reassign the `type` as the `event_type` parameter
                workflow_source["type"] = workflow_source["parameters"]["event_type"]
                workflow_source["connector_type"] = "Flexli:CoreV1:CustomEvent"
            else:
                workflow_source["connector_type"] = workflow_source["type"]

        else:
            connector_id = workflow_source["connector_id"]

            if not (
                matched_source_connector := find_item_by_key(
                    items=current_tenant_connectors, key="id", value=connector_id
                )
            ):
                raise BadRequest(
                    error_code="InvalidConnectorId",
                    description="An invalid connector was provided",
                    details={"id": connector_id},
                )

            # if workflow_source["type"] not in matched_source_connector["context"]["events"]:
            if (
                workflow_source["type"]
                not in matched_source_connector["context"]["events"]
            ):
                raise BadRequest(
                    error_code="UnsupportedEventType",
                    description="The source event type is not supported by this connector",
                    details={
                        "connector": {
                            "id": matched_source_connector["id"],
                            "type": matched_source_connector["type"],
                        },
                        "event_type": workflow_source["type"],
                    },
                )

            # matched_source_connector_data = find_connector_by_id(
            #     tenant_id=tenant_id,
            #     connector_id=connector_id,
            #     connectors_list=current_tenant_connectors,
            # )

            # TODO: Update middleware to handle JSON schema validation errors.
            workflow_source["connector_type"] = matched_source_connector["type"]

    # TODO: This needs to also process actions within `Flexli:CoreV1:Iterator`
    for workflow_action in workflow_data["actions"]:
        if workflow_action["type"].startswith("Flexli:CoreV1:"):
            # Pydantic model currently validates
            # TODO: Replace Pydantic models in input validation with an embedded JSON schema
            # The embedded JSON schema will be able to leverage the processing below

            # TODO: Convert to using `{ConId}:{ConType}:{ActType}` for action types
            workflow_action["connector_id"] = "Flexli:CoreV1"
            workflow_action["connector_type"] = workflow_action["type"]
            continue

        connector_id = workflow_action["connector_id"]

        if not (
            matched_action_connector := find_item_by_key(
                items=current_tenant_connectors, key="id", value=connector_id
            )
        ):
            raise BadRequest(
                error_code="InvalidConnectorId",
                description="An invalid connector was provided",
                details={"id": connector_id},
            )

        if (
            workflow_action["type"]
            not in matched_action_connector["context"]["actions"]
        ):
            raise BadRequest(
                error_code="UnsupportedActionType",
                description="The action type is not supported by this connector",
                details={
                    "connector": {
                        "id": matched_action_connector["id"],
                        "type": matched_action_connector["type"],
                    },
                    "action_type": workflow_action["type"],
                },
            )

        matched_action_connector_data = find_item_by_key(
            items=find_connector_by_id(
                tenant_id=tenant_id,
                connector_id=connector_id,
                connectors_list=current_tenant_connectors,
            )["actions"],
            key="type",
            value=workflow_action["type"],
        )

        if actions_validation_errors := json_schema_validation(
            data=workflow_action.get("parameters"),
            validator=Draft202012Validator(
                matched_action_connector_data["parameters"],
                format_checker=FormatChecker(),
            ),
        ):
            raise BadRequest(
                error_code="ActionParameterValidationError",
                description="The action parameters did not pass validation",
                details={
                    "connector": {
                        "id": matched_action_connector["id"],
                        "type": matched_action_connector["type"],
                    },
                    "action_type": workflow_action["type"],
                    "errors": actions_validation_errors,
                },
            )

        workflow_action["connector_type"] = matched_action_connector["type"]

    new_workflow_id = create_workflow(
        dynamodb_table,
        tenant_id=tenant_id,
        data=workflow_data,
    )

    return ApiResponse(
        201,
        {"id": new_workflow_id, "href": f"/v1/workflows/{new_workflow_id}"},
    )
