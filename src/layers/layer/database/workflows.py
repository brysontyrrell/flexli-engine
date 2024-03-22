from typing import Optional, Union

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from ulid import ULID

from apis.models import NotFound


def create_workflow(table_resource, tenant_id: str, data: dict) -> str:
    """Write a new workflow for a tenant to the database."""
    workflow_id = str(ULID())

    # TODO: Needs to be transaction to write the release item
    table_item_keys = {
        "pk": f"T#{tenant_id}#W#{workflow_id}",
        "sk": "V#1",
        "lsi1pk": f"T#{tenant_id}#W",
        "lsi1sk": f"W#{workflow_id}#V#1",
        "id": workflow_id,
        "version": 1,
        "is_release_version": True,
        "metadata": {"tenant_id": tenant_id},
    }

    # GSI1 is only populated if a new workflow is enabled and is an event type
    # (this GSI should only exist on the release version)
    if (
        data.get("source") is not None
        and data["enabled"] is True
        and data["source"]["connector_type"] not in ["Flexli:CoreV1:Schedule"]
    ):
        table_item_keys.update(
            {
                "gsi1pk": f"T#{tenant_id}#C#{data['source']['connector_id']}",
                "gsi1sk": f"E#{data['source']['type']}",
            }
        )

    table_resource.put_item(
        Item=dict(
            **table_item_keys,
            **data,
        ),
        ConditionExpression="attribute_not_exists(sk)",
    )

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
