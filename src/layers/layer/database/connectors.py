from functools import lru_cache
import os
import time

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from ulid import ULID

from apis.models import BadRequest, NotFound
from aws_utils import get_boto3_resource

TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb_table = get_boto3_resource("dynamodb").Table(TABLE_NAME)


def create_connector(tenant_id: str, data: dict) -> str:
    """Write a new connector for a tenant to the database.

    Database write generates the ID and a context key containing lists of the event and action types.
    """
    connector_id = str(ULID())
    data["context"] = {"events": [], "actions": []}

    try:
        for i in data.get("events", []):
            data["context"]["events"].append(i["type"])
    except (KeyError, TypeError):
        pass

    try:
        for i in data.get("actions", []):
            data["context"]["actions"].append(i["type"])
    except (KeyError, TypeError):
        pass

    dynamodb_table.put_item(
        Item=dict(
            {
                "pk": f"T#{tenant_id}#C#{connector_id}",
                "sk": "A",
                "_item_type": "ConnectorVersion",
                "lsi1pk": f"T#{tenant_id}#C",
                "lsi1sk": f"C#{connector_id}",
                "id": connector_id,
                "version": 1,
                "metadata": {
                    "tenant_id": tenant_id,
                    "created_at": int(time.time()),
                },
            },
            **data,
        ),
        ConditionExpression=Attr("sk").not_exists(),
    )
    return connector_id


def read_connector(tenant_id: str, connector_id: str) -> dict:
    """Read a connector for a tenant from the database."""
    response = dynamodb_table.get_item(
        Key={"pk": f"T#{tenant_id}#C#{connector_id}", "sk": "A"}
    )
    try:
        return response["Item"]
    except KeyError:
        raise NotFound("Connector not found", details={"id": connector_id})


# TODO: Switch to TLRU caching
@lru_cache
def read_connector_cached(tenant_id: str, connector_id: str) -> dict:
    return read_connector(tenant_id=tenant_id, connector_id=connector_id)


def delete_connector(tenant_id: str, connector_id: str) -> None:
    """Delete a connector for a tenant from the database."""
    # TODO: Must ensure connector is not linked to ANY workflows to be allowed!
    try:
        dynamodb_table.delete_item(
            Key={"pk": f"T#{tenant_id}#C#{connector_id}", "sk": "A"},
            ConditionExpression=Attr("sk").exists(),
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFound("Connector not found", details={"id": connector_id})
        else:
            raise


def list_connectors(tenant_id: str) -> list[dict]:
    """List connectors for a tenant from the database."""
    response = dynamodb_table.query(
        IndexName="LSI1",
        KeyConditionExpression=Key("lsi1pk").eq(f"T#{tenant_id}#C"),
    )
    return response["Items"]


def find_connector_by_id(
    tenant_id: str, connector_id: str, connectors_list: list[dict]
) -> dict:
    """Return a (cached) connector object in a list of connectors using the provided ID.
    Reference ``ConnectorsListItem`` for object attributes.
    """
    if next(
        (i for i in connectors_list if i["id"] == connector_id),
        None,
    ):
        return read_connector_cached(tenant_id=tenant_id, connector_id=connector_id)
    else:
        raise BadRequest(
            error_code="InvalidConnectorId",
            description="An invalid connector was provided",
            details={"id": connector_id},
        )
