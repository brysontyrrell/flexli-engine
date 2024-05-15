import json
import os
from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
import boto3
from botocore.exceptions import ClientError

from apis.models import DecimalEncoder

RUN_QUEUE_ARN = os.environ["RUN_QUEUE_ARN"]
SCHEDULER_ROLE_ARN = os.environ["SCHEDULER_ROLE_ARN"]

logger = Logger()

client = boto3.client("scheduler")


@event_source(data_class=DynamoDBRecord)
def create_handler(event: DynamoDBRecord, context):
    create_schedule(image=event.dynamodb.new_image)


@event_source(data_class=DynamoDBRecord)
def delete_handler(event: DynamoDBRecord, context):
    delete_schedule(image=event.dynamodb.old_image)


@event_source(data_class=DynamoDBRecord)
def modified_handler(event: DynamoDBRecord, context):
    new_image = event.dynamodb.new_image
    old_image = event.dynamodb.old_image

    new_image_enabled = new_image["enabled"]
    old_image_enabled = old_image["enabled"]

    new_image_source = new_image.get("source", {})
    old_image_source = old_image.get("source", {})

    new_image_source_type = new_image_source.get("type")
    old_image_source_type = old_image_source.get("type")

    # Modified - Shallow dict comparison works here
    if (
        new_image_enabled
        and old_image_enabled
        and new_image_source_type == "Flexli:CoreV1:Schedule"
        and old_image_source_type == "Flexli:CoreV1:Schedule"
        and new_image_source.get("parameters") != old_image_source.get("parameters")
    ):
        logger.info("Updating existing schedule")
        update_schedule(image=new_image)
    # Enabled
    elif (
        new_image_enabled
        and not old_image_enabled
        and new_image_source_type == "Flexli:CoreV1:Schedule"
        and old_image_source_type == "Flexli:CoreV1:Schedule"
    ):
        logger.info("Creating schedule (enabled)")
        create_schedule(image=new_image)
    # Disabled
    elif (
        not new_image_enabled
        and old_image_enabled
        and new_image_source_type == "Flexli:CoreV1:Schedule"
        and old_image_source_type == "Flexli:CoreV1:Schedule"
    ):
        logger.info("Deleting schedule (disabled)")
        delete_schedule(image=new_image)
    # Added
    elif (
        new_image_enabled
        and new_image_source_type == "Flexli:CoreV1:Schedule"
        and old_image_source_type != "Flexli:CoreV1:Schedule"
    ):
        logger.info("Creating schedule")
        create_schedule(image=new_image)
    # Removed
    elif (
        old_image_enabled
        and old_image_source_type == "Flexli:CoreV1:Schedule"
        and new_image_source_type != "Flexli:CoreV1:Schedule"
    ):
        logger.info("Deleting schedule")
        delete_schedule(image=new_image)
    else:
        logger.warning("NO OP")


def schedule_expression(image: dict[str, Any]):
    if source_cron := image["source"]["parameters"].get("cron"):
        return f"cron({source_cron})"
    elif source_rate := image["source"]["parameters"].get("rate"):
        return f"rate({source_rate})"
    else:
        # This should not be reachable
        raise


def create_schedule(image: dict[str, Any]):
    tenant_id = image["metadata"]["tenant_id"]

    # TODO: Schedule groups must already exists - can only contain letters (no numbers, no ULID)
    response = client.create_schedule(
        Name=f"{tenant_id}-{image['id']}",
        # GroupName=tenant_id,
        # Description="string",
        # ClientToken="string",
        ScheduleExpression=schedule_expression(image=image),
        # ScheduleExpressionTimezone="UTC",
        FlexibleTimeWindow={"Mode": "OFF"},
        State="ENABLED",
        Target={
            "Arn": RUN_QUEUE_ARN,
            "RoleArn": SCHEDULER_ROLE_ARN,
            "Input": json.dumps(
                {
                    "tenant_id": tenant_id,
                    "workflow_id": image["id"],
                    "workflow_version": image["version"],
                    # "workflow_schema_version": "",
                    "workflow_name": image["name"],
                    "run_id": None,
                    "source_input": {},
                    "actions": image["actions"],
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
    logger.debug(response)


def delete_schedule(image: dict[str, Any]):
    tenant_id = image["metadata"]["tenant_id"]

    try:
        response = client.delete_schedule(Name=f"{tenant_id}-{image['id']}")
    except ClientError as error:
        # ResourceNotFoundException
        logger.warning(error)
    else:
        logger.info(response)


def update_schedule(image: dict[str, Any]):
    tenant_id = image["metadata"]["tenant_id"]

    response = client.update_schedule(
        Name=f"{tenant_id}-{image['id']}",
        ScheduleExpression=schedule_expression(image=image),
        FlexibleTimeWindow={"Mode": "OFF"},
        State="ENABLED",
        Target={
            "Arn": RUN_QUEUE_ARN,
            "RoleArn": SCHEDULER_ROLE_ARN,
            "Input": json.dumps(
                {
                    "tenant_id": tenant_id,
                    "workflow_id": image["id"],
                    "workflow_version": image["version"],
                    # "workflow_schema_version": "",
                    "workflow_name": image["name"],
                    "run_id": None,
                    "source_input": {},
                    "actions": image["actions"],
                },
                cls=DecimalEncoder,
            ),
        },
    )
    logger.debug(response)
