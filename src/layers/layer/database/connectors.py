from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from ulid import ULID

from apis.models import NotFound


def create_connector(table_resource, tenant_id: str, data: dict) -> str:
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

    table_resource.put_item(
        Item=dict(
            {
                "pk": f"T#{tenant_id}#C#{connector_id}",
                "sk": "A",
                "lsi1pk": f"T#{tenant_id}#C",
                "lsi1sk": f"C#{connector_id}",
                "id": connector_id,
                "version": 1,
            },
            **data,
        ),
        ConditionExpression=Attr("sk").not_exists(),
    )
    return connector_id


def read_connector(table_resource, tenant_id: str, connector_id: str) -> dict:
    """Read a connector for a tenant from the database."""
    response = table_resource.get_item(
        Key={"pk": f"T#{tenant_id}#C#{connector_id}", "sk": "A"}
    )
    try:
        return response["Item"]
    except KeyError:
        raise NotFound("Connector not found", details={"id": connector_id})


def delete_connector(table_resource, tenant_id: str, connector_id: str) -> None:
    """Delete a connector for a tenant from the database."""
    # TODO: Must ensure connector is not linked to ANY workflows to be allowed!
    try:
        table_resource.delete_item(
            Key={"pk": f"T#{tenant_id}#C#{connector_id}", "sk": "A"},
            ConditionExpression=Attr("sk").exists(),
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFound("Connector not found", details={"id": connector_id})
        else:
            raise


def list_connectors(table_resource, tenant_id: str) -> list[dict]:
    """List connectors for a tenant from the database."""
    response = table_resource.query(
        IndexName="LSI1",
        KeyConditionExpression=Key("lsi1pk").eq(f"T#{tenant_id}#C"),
    )
    return response["Items"]
