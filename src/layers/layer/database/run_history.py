from typing import Optional

from boto3.dynamodb.conditions import Key


def list_run_history(
    table_resource,
    tenant_id: str,
    workflow_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """Return run history items. If a workflow ID is provided only runs for that workflow are
    returned. If a limit is provided only that number of items is returned.
    """
    if workflow_id:
        query_params = {
            "KeyConditionExpression": Key("pk").eq(f"T#{tenant_id}#WH#{workflow_id}")
        }
    else:
        query_params = {
            "IndexName": "GSI1",
            "KeyConditionExpression": Key("gsi1pk").eq(f"T#{tenant_id}#WH"),
        }

    query_params["ScanIndexForward"] = False

    if limit:
        query_params["Limit"] = limit

    response = table_resource.query(**query_params)

    return response["Items"]


def list_run_history_by_id(
    table_resource,
    tenant_id: str,
    run_id: str,
    limit: Optional[int] = None,
) -> list[dict]:
    """Return run history items by run ID. If a limit is provided only that number of items is
    returned.
    """
    query_params = {
        "KeyConditionExpression": Key("pk").eq(f"T#{tenant_id}#RH#{run_id}")
        & Key("sk").begins_with("TS#")
    }

    if limit:
        query_params["Limit"] = limit

    response = table_resource.query(**query_params)

    return response["Items"]
