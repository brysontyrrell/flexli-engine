import logging
import os
import time
from typing import Optional, Union

from boto3.dynamodb.conditions import Attr, Key
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError
from ulid import ULID

from apis.models import NotFound
from aws_utils import get_boto3_client, get_boto3_resource

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_client = get_boto3_client("dynamodb")
dynamodb_table = get_boto3_resource("dynamodb").Table(TABLE_NAME)

type_serializer = TypeSerializer()


def create_workflow(tenant_id: str, data: dict) -> str:
    """Write a new workflow for a tenant to the database."""
    transaction_items = []
    workflow_id = str(ULID())

    workflow_item = dict(
        {
            "id": workflow_id,
            "version": 1,
            "is_release_version": True,
            "metadata": {
                "tenant_id": tenant_id,
                "created_at": int(time.time()),
            },
        },
        **data,
    )

    workflow_a_item = dict(
        {
            "pk": f"T#{tenant_id}#W#{workflow_id}",
            "sk": "V#1",
            "_item_type": "WorkflowVersion",
            "lsi1pk": f"T#{tenant_id}#W",
            "lsi1sk": f"W#{workflow_id}#V#1",
        },
        **workflow_item,
    )

    workflow_r_item = dict(
        {
            "pk": f"T#{tenant_id}#W#{workflow_id}",
            "sk": "R",
            "_item_type": "WorkflowReleaseVersion",
            "lsi1pk": f"T#{tenant_id}#W#R",
            "lsi1sk": f"W#{workflow_id}",
        },
        **workflow_item,
    )

    # Release item GSI1 is only populated if the workflow is enabled and is an event type
    # (this GSI only exists on the release item)
    if (
        data.get("source") is not None
        and data["enabled"] is True
        and data["source"]["connector_type"] not in ["Flexli:CoreV1:Schedule"]
    ):
        workflow_r_item.update(
            {
                "gsi1pk": f"T#{tenant_id}#C#{data['source']['connector_id']}",
                "gsi1sk": f"E#{data['source']['type']}",
            }
        )

    transaction_items.append(
        {
            "Put": {
                "Item": type_serializer.serialize(workflow_a_item)["M"],
                "ConditionExpression": f"attribute_not_exists(sk)",
                "TableName": TABLE_NAME,
            },
        }
    )

    # Workflow Release Version item
    transaction_items.append(
        {
            "Put": {
                "Item": type_serializer.serialize(workflow_r_item)["M"],
                "TableName": TABLE_NAME,
            },
        }
    )
    logging.debug(transaction_items)

    dynamodb_client.transact_write_items(TransactItems=transaction_items)
    return workflow_id


def read_workflow_version(
    table_resource, tenant_id: str, workflow_id: str, workflow_version: str
) -> dict:
    """Read a workflow version for a tenant from the database."""
    response = table_resource.get_item(
        Key={
            "pk": f"T#{tenant_id}#W#{workflow_id}",
            "sk": f"V#{workflow_version}",
        }
    )
    try:
        return response["Item"]
    except KeyError:
        raise NotFound(
            "Workflow version not found",
            details={"id": workflow_id, "version": workflow_version},
        )


def read_workflow_release_version(
    table_resource, tenant_id: str, workflow_id: str
) -> Union[dict, None]:
    """Read a workflow's release version for a tenant from the database."""
    response = table_resource.get_item(
        Key={"pk": f"T#{tenant_id}#W#{workflow_id}", "sk": "R"}
    )
    try:
        return response["Item"]
    except KeyError:
        raise NotFound(
            "Workflow does not have a release version",
            details={"id": workflow_id},
        )


def delete_workflow_version(
    table_resource, tenant_id: str, workflow_id: str, workflow_version: str
) -> None:
    """Delete a workflow version for a tenant from the database."""
    # TODO: If deleting a release, it must be the LAST version of the workflow
    # list_workflows | limit 2
    # if is_release_version and versions > 1 -> Conflict
    try:
        table_resource.delete_item(
            Key={
                "pk": f"T#{tenant_id}#W#{workflow_id}",
                "sk": f"V#{workflow_version}",
            },
            ConditionExpression=Attr("sk").exists(),
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFound(
                "Workflow version not found",
                details={"id": workflow_id, "version": workflow_version},
            )
        else:
            raise


def list_workflows(
    table_resource,
    tenant_id: str,
    workflow_id: Optional[str] = None,
    releases_only: Optional[bool] = None,
) -> list[dict]:
    """List workflows for a tenant from the database.

    By default, this will return all workflow versions for a tenant.
    Passing a 'workflow_id' will return all workflow versions only for that ID.
    Passing 'releases_only=True' will return only release workflow versions.
    Passing a 'workflow_id' and 'releases_only=True' will return the release version of the workflow.
    """
    if workflow_id and (releases_only is True):
        # Query the release version of a workflow by ID
        query_params = {
            "IndexName": "LSI1",
            "KeyConditionExpression": Key("lsi1pk").eq(f"T#{tenant_id}#W#R")
            & Key("lsi1sk").begins_with(f"W#{workflow_id}"),
        }
    elif (not workflow_id) and (releases_only is True):
        # Query all release versions
        query_params = {
            "IndexName": "LSI1",
            "KeyConditionExpression": Key("lsi1pk").eq(f"T#{tenant_id}#W#R")
            & Key("lsi1sk").begins_with("W#"),
        }
    elif workflow_id:
        # Query all versions of a workflow ID
        query_params = {
            "KeyConditionExpression": Key("pk").eq(f"T#{tenant_id}#W#{workflow_id}")
            & Key("sk").begins_with("V#"),
        }
    else:
        # List all workflow versions
        query_params = {
            "IndexName": "LSI1",
            "KeyConditionExpression": Key("lsi1pk").eq(f"T#{tenant_id}#W"),
        }

    response = table_resource.query(
        **query_params,
        ProjectionExpression="id, #n, description, version, is_release_version, schema_version",
        ExpressionAttributeNames={"#n": "name"},
    )

    return response["Items"]
