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
    modified_release = event.dynamodb.new_image
    previous_release = event.dynamodb.old_image
    tenant_id = modified_release["metadata"]["tenant_id"]

    # Shallow dict comparison works here
    if (
        modified_release["source"]["parameters"]
        == previous_release["source"]["parameters"]
    ):
        print("NO OP")
        return

    if source_cron := modified_release["source"]["parameters"].get("cron"):
        schedule_expression = f"cron({source_cron})"
    elif source_rate := modified_release["source"]["parameters"].get("rate"):
        schedule_expression = f"rate({source_rate})"
    else:
        raise

    # TODO: Compare parameter values. If different, update the schedule.
    response = client.update_schedule(
        Name=f"{modified_release['id']}-v{modified_release['version']}",
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
                    "workflow_id": modified_release["id"],
                    "workflow_version": modified_release["version"],
                    # "workflow_schema_version": "",
                    "workflow_name": modified_release["name"],
                    "run_id": None,
                    "source_input": {},
                    "actions": modified_release["actions"],
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
