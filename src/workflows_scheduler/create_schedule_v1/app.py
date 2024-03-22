import json
import os

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
import boto3

from apis.models import DecimalEncoder

RUN_QUEUE_ARN = os.environ["RUN_QUEUE_ARN"]
SCHEDULER_ROLE_ARN = os.environ["SCHEDULER_ROLE_ARN"]

client = boto3.client("scheduler")


@event_source(data_class=DynamoDBRecord)
def lambda_handler(event: DynamoDBRecord, context):
    workflow = event.dynamodb.new_image
    tenant_id = workflow["metadata"]["tenant_id"]

    if source_cron := workflow["source"]["parameters"].get("cron"):
        schedule_expression = f"cron({source_cron})"
    elif source_rate := workflow["source"]["parameters"].get("rate"):
        schedule_expression = f"rate({source_rate})"
    else:
        raise

    # TODO: Schedule groups must already exists - can only contain letters (no numbers, no ULID)
    response = client.create_schedule(
        Name=f"{workflow['id']}-v{workflow['version']}",
        # GroupName=tenant_id,
        # Description="string",
        # ClientToken="string",
        ScheduleExpression=schedule_expression,
        # ScheduleExpressionTimezone="UTC",
        FlexibleTimeWindow={"Mode": "OFF"},
        State="ENABLED",
        Target={
            "Arn": RUN_QUEUE_ARN,
            "RoleArn": SCHEDULER_ROLE_ARN,
            "Input": json.dumps(
                {
                    "tenant_id": tenant_id,
                    "workflow_id": workflow["id"],
                    "workflow_version": workflow["version"],
                    # "workflow_schema_version": "",
                    "workflow_name": workflow["name"],
                    "run_id": None,  # TODO: Runner must generate Run IDs if this is `null`
                    "source_input": {},
                    "actions": workflow["actions"],
                },
                cls=DecimalEncoder,
            ),
            # "DeadLetterConfig": {"Arn": "string"},
            # "RetryPolicy": {
            #     "MaximumEventAgeInSeconds": 123,
            #     "MaximumRetryAttempts": 123,
            # },
        },
    )
    print(response)
