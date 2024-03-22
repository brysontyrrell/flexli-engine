from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
import boto3
from botocore.exceptions import ClientError

logger = Logger()

client = boto3.client("scheduler")


@event_source(data_class=DynamoDBRecord)
def lambda_handler(event: DynamoDBRecord, context):
    workflow = event.dynamodb.old_image
    # tenant_id = workflow["metadata"]["tenant_id"]

    try:
        response = client.delete_schedule(
            # ClientToken='string',
            # GroupName='string',
            Name=f"{workflow['id']}-v{workflow['version']}",
        )
    except ClientError as error:
        # ResourceNotFoundException
        logger.warning(error)
    else:
        logger.info(response)
